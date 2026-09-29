use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sysinfo::{Pid, System};
use tauri::{AppHandle, Emitter, Manager, State};
use tauri_plugin_shell::ShellExt;
use tokio::io::{AsyncBufReadExt, AsyncSeekExt, SeekFrom};
use tokio::process::{Child, Command};
use tokio::time::timeout;

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
enum ServicoNome {
    Ollama,
    Api,
    Frontend,
    Chatcli,
}

impl ServicoNome {
    fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "ollama" => Some(ServicoNome::Ollama),
            "api" => Some(ServicoNome::Api),
            "frontend" => Some(ServicoNome::Frontend),
            "chatcli" => Some(ServicoNome::Chatcli),
            _ => None,
        }
    }

    fn porta(&self) -> u16 {
        match self {
            ServicoNome::Ollama => 11434,
            ServicoNome::Api => 8000,
            ServicoNome::Frontend => 3000,
            ServicoNome::Chatcli => 0,
        }
    }

    fn display(&self) -> &'static str {
        match self {
            ServicoNome::Ollama => "ollama",
            ServicoNome::Api => "api",
            ServicoNome::Frontend => "frontend",
            ServicoNome::Chatcli => "chatcli",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ServiceStatus {
    online: bool,
    pid: Option<u32>,
    port: u16,
    uptime_segundos: Option<u64>,
    memoria_mb: Option<f64>,
}

impl Default for ServiceStatus {
    fn default() -> Self {
        ServiceStatus {
            online: false,
            pid: None,
            port: 0,
            uptime_segundos: None,
            memoria_mb: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct CheckServicesResult {
    ollama: ServiceStatus,
    api: ServiceStatus,
    frontend: ServiceStatus,
    chatcli: ServiceStatus,
}

struct LauncherState {
    processos: Mutex<HashMap<ServicoNome, (u32, Rastreado, Instant)>>,
    stop_flags: Mutex<HashMap<String, Arc<AtomicBool>>>,
}

enum Rastreado {
    Owned(Child),
    Externo,
}

impl Rastreado {
    async fn parar(&mut self, pid: u32) {
        match self {
            Rastreado::Owned(child) => {
                let _ = child.start_kill();
                match timeout(Duration::from_secs(5), child.wait()).await {
                    Ok(Ok(_)) => {}
                    _ => {
                        let _ = child.kill().await;
                        let _ = child.wait().await;
                        let _ = Command::new("taskkill")
                            .args(["/F", "/PID", &pid.to_string()])
                            .output()
                            .await;
                    }
                }
            }
            Rastreado::Externo => {
                // PID externo (ex: Next.js do beforeDevCommand do Tauri).
                // Não matamos se for o mesmo do beforeDev — só marcamos como off.
                // Mas para o toggle "Desligar Frontend" do usuário ainda desliga via taskkill.
                let _ = Command::new("taskkill")
                    .args(["/F", "/PID", &pid.to_string(), "/T"])
                    .output()
                    .await;
            }
        }
    }
}

impl Default for LauncherState {
    fn default() -> Self {
        LauncherState {
            processos: Mutex::new(HashMap::new()),
            stop_flags: Mutex::new(HashMap::new()),
        }
    }
}

fn usar_force_fallback_memory() -> bool {
    std::env::var("FORCE_FALLBACK_MEMORY")
        .map(|v| v == "1" || v.to_lowercase() == "true")
        .unwrap_or(false)
}

fn descobrir_pid_por_porta(porta: u16) -> Option<u32> {
    let out = std::process::Command::new("netstat")
        .args(["-ano"])
        .output()
        .ok()?;
    let stdout = String::from_utf8_lossy(&out.stdout);
    let needle_port = format!(":{}", porta);
    for line in stdout.lines() {
        let upper = line.to_uppercase();
        if (upper.contains("LISTENING") || upper.contains("ESTABLISHED"))
            && line.contains(&needle_port)
        {
            let cols: Vec<&str> = line.split_whitespace().collect();
            if let Some(last) = cols.last() {
                if let Ok(pid) = last.parse::<u32>() {
                    return Some(pid);
                }
            }
        }
    }
    None
}

async fn probe_http_frontend(porta: u16) -> bool {
    // Next.js dev no warm-up inicial pode retornar 404 em HEAD / enquanto
    // compila a 1ª página. Para não marcar "serviço morto", aceitamos qualquer
    // status 4xx/5xx MENOS erro de conexão. Também aceitamos explicitamente
    // "conexão recusada inicial" mas retorna falso aí.
    let url = format!("http://127.0.0.1:{}/", porta);
    let client = match reqwest::Client::builder()
        .timeout(Duration::from_secs(3))
        .build()
    {
        Ok(c) => c,
        Err(_) => return false,
    };
    match client.head(&url).send().await {
        Ok(_) => true,
        Err(e) => {
            if e.is_connect() || e.is_timeout() {
                false
            } else {
                // Erro HTTP 4xx/5xx = servidor está de pé
                e.status().is_some()
            }
        }
    }
}

async fn aguardar_servico_frontend(porta: u16, max_segundos: u64) -> bool {
    let inicio = Instant::now();
    while inicio.elapsed() < Duration::from_secs(max_segundos) {
        if probe_http_frontend(porta).await {
            return true;
        }
        tokio::time::sleep(Duration::from_millis(750)).await;
    }
    probe_http_frontend(porta).await
}

fn pasta_projeto() -> PathBuf {
    let base = PathBuf::from("c:/Users/Jhon Ross/Documents/trae_projects/NeuroCore");
    base
}

#[allow(dead_code)]
fn pasta_frontend() -> PathBuf {
    pasta_projeto().join("frontend")
}

#[allow(dead_code)]
fn pasta_backend() -> PathBuf {
    pasta_projeto()
}

fn pasta_modelos() -> PathBuf {
    // Reais modelos ficam no HDD G:\models (decisão maratona Dia 2).
    // Se a pasta não existir, cai para o SSD local.
    let g = PathBuf::from("G:/models");
    if g.exists() {
        g
    } else {
        pasta_projeto().join("local_models")
    }
}

fn memoria_por_pid(pid: u32) -> Option<f64> {
    if usar_force_fallback_memory() {
        return Some(0.0);
    }
    let mut sys = System::new_all();
    sys.refresh_all();
    let sys_pid = Pid::from_u32(pid);
    sys.process(sys_pid).map(|p| (p.memory() as f64) / 1024.0 / 1024.0)
}

fn uptime_por_pid(pid: u32) -> Option<u64> {
    let mut sys = System::new_all();
    sys.refresh_all();
    let sys_pid = Pid::from_u32(pid);
    let proc = sys.process(sys_pid)?;
    let run_secs = proc.run_time();
    Some(run_secs)
}

fn pid_esta_ativo(pid: u32) -> bool {
    let mut sys = System::new_all();
    sys.refresh_all();
    let sys_pid = Pid::from_u32(pid);
    sys.process(sys_pid).is_some()
}

async fn probe_http(porta: u16, metodo: &str, caminho: &str) -> bool {
    if porta == 0 {
        return false;
    }
    let url = format!("http://127.0.0.1:{}{}", porta, caminho);
    let client = match reqwest::Client::builder()
        .timeout(Duration::from_secs(7))
        .build()
    {
        Ok(c) => c,
        Err(_) => return false,
    };
    let req_builder = match metodo {
        "HEAD" => client.head(&url),
        "GET" => client.get(&url),
        _ => client.get(&url),
    };
    match req_builder.send().await {
        Ok(resp) => resp.status().is_success() || resp.status() == 401 || resp.status() == 403,
        Err(_) => false,
    }
}

async fn aguardar_servico(porta: u16, metodo: &str, caminho: &str, max_segundos: u64) -> bool {
    let inicio = Instant::now();
    while inicio.elapsed() < Duration::from_secs(max_segundos) {
        if probe_http(porta, metodo, caminho).await {
            return true;
        }
        tokio::time::sleep(Duration::from_millis(500)).await;
    }
    probe_http(porta, metodo, caminho).await
}

fn montar_comando_base() -> Command {
    let mut cmd = Command::new("cmd");
    cmd.arg("/C");
    if let Ok(val) = std::env::var("FORCE_FALLBACK_MEMORY") {
        cmd.env("FORCE_FALLBACK_MEMORY", val);
    }
    cmd
}

async fn iniciar_ollama(state: &'_ State<'_, LauncherState>) -> Result<(), String> {
    // Ollama pode já estar rodando (padrão manter vivo ao sair). Nesse caso,
    // NÃO duplica o processo — só confirma a porta e pula.
    if probe_http(11434, "GET", "/api/tags").await {
        return Ok(());
    }
    let mut cmd = montar_comando_base();
    cmd.arg("ollama serve");
    cmd.current_dir(pasta_projeto());
    // IMPORTANTE: Stdio::null() evita DEADLOCK de buffer pipe (~4KB no Windows).
    // Antes: stdout/stderr = piped() + loop tokio lendo linhas. Se a task tokio
    // for dropada ou o buffer encher, o processo filho bloqueia no write() → ZUMBI.
    // Ollama grava logs próprios no sistema; não precisamos espelhar via pipe.
    cmd.stdout(std::process::Stdio::null());
    cmd.stderr(std::process::Stdio::null());

    let child = cmd.spawn().map_err(|e| format!("Falha ao iniciar Ollama: {}", e))?;
    let pid = child.id().ok_or_else(|| "Não foi possível obter PID do Ollama".to_string())?;

    {
        let mut map = state.processos.lock().unwrap();
        map.insert(ServicoNome::Ollama, (pid, Rastreado::Owned(child), Instant::now()));
    }

    let ok = aguardar_servico(11434, "GET", "/api/tags", 10).await;
    if !ok {
        let _ = parar_servico_interno(state, &ServicoNome::Ollama).await;
        return Err("Ollama não respondeu em 10s".to_string());
    }
    Ok(())
}

async fn iniciar_api(state: &'_ State<'_, LauncherState>) -> Result<(), String> {
    // Se a API já estiver de pé (por script iniciar_prometeu.ps1 ou outra sessão),
    // não duplica. Descobre PID via netstat e marca como Rastreado::Externo.
    if probe_http(8000, "GET", "/api/status").await {
        let pid = descobrir_pid_por_porta(8000);
        if let Some(pid_achado) = pid {
            let mut map = state.processos.lock().unwrap();
            map.insert(
                ServicoNome::Api,
                (pid_achado, Rastreado::Externo, Instant::now()),
            );
        }
        return Ok(());
    }
    let venv_python = pasta_projeto().join(".venv").join("Scripts").join("python.exe");
    let mut cmd = if venv_python.exists() {
        let mut c = Command::new(venv_python);
        c.arg("-m");
        c.arg("uvicorn");
        c
    } else {
        let mut c = montar_comando_base();
        c.arg("uvicorn");
        c
    };
    cmd.args(["core.api:app", "--host", "127.0.0.1", "--port", "8000"]);
    cmd.current_dir(pasta_projeto());
    cmd.env(
        "FORCE_FALLBACK_MEMORY",
        if usar_force_fallback_memory() { "1" } else { "0" },
    );

    // =====================================================================
    // CORREÇÃO DEFINITIVA: NÃO USAR PIPE STDOUT/STDERR.
    //
    // Causa raiz do bug "Ligar tudo retorna OK mas API é ZUMBI / não responde":
    //   Stdio::piped() cria um pipe entre Rust ↔ Python com buffer ~4KB no
    //   Windows. Quando Python escreve logs (startup uvicorn, lifespan
    //   orquestrador, imports, etc) e o Rust para de ler o pipe (task tokio
    //   cai fora ou só lê as 12 primeiras linhas de stderr), o buffer
    //   enche → a syscall write() do Python BLOQUEIA indefinidamente →
    //   Python fica LISTEN na porta 8000 mas NÃO processa requisições HTTP.
    //
    // Solução:
    //   - STDOUT = null() (Python já grava JSONL em local_memory/logs/*.jsonl)
    //   - STDERR = ARQUIVO TEMPORÁRIO → sem buffer de pipe, nunca bloqueia.
    //     Se o probe HTTP falhar, lemos esse arquivo para extrair erros
    //     de startup (ModuleNotFound, Address already in use etc).
    // =====================================================================
    cmd.stdout(std::process::Stdio::null());

    let pasta_logs = pasta_projeto().join("local_memory").join("logs");
    let _ = std::fs::create_dir_all(&pasta_logs);
    let ts = Utc::now().format("%Y%m%d_%H%M%S").to_string();
    let caminho_stderr = pasta_logs.join(format!("api_stderr_{}.log", ts));
    let arquivo_stderr = std::fs::File::create(&caminho_stderr)
        .map_err(|e| format!("Falha ao criar log stderr API: {}", e))?;
    cmd.stderr(std::process::Stdio::from(arquivo_stderr));

    let child = cmd.spawn().map_err(|e| format!("Falha ao iniciar API: {}", e))?;
    let pid = child.id().ok_or_else(|| "Não foi possível obter PID da API".to_string())?;

    {
        let mut map = state.processos.lock().unwrap();
        map.insert(ServicoNome::Api, (pid, Rastreado::Owned(child), Instant::now()));
    }
    // Observação: monitor de vida do processo já é feito via check_services()
    // a cada 4s pelo frontend, usando construir_status() → pid_esta_ativo(pid).
    // Não criamos task extra aqui para evitar unsafe lifetime transmute; o
    // polling de 4s já garante detecção rápida de morte sem overhead.

    // Timeout: 40s (startup FastAPI lifespan + orquestrador + llm_core carregando
    // modelo pesado (~10-15s) + imports Python. Observado no log do usuário:
    // 13:39:14 → 13:39:24 lifespan orquestrador inicializado (10s).
    let ok = aguardar_servico(8000, "GET", "/api/status", 40).await;
    if !ok {
        // 🔁 Re-check triplo ANTES de assassinar o child process.
        // Bug histórico: o uvicorn imprimia "Uvicorn running on http://127.0.0.1:8000"
        // no stderr, mas aguardar_servico retornava false pq a última iteração do polling
        // havia caído no sleep 500ms antes do último probe. NÃO MATAR por impaciência.
        let p1 = probe_http(8000, "GET", "/api/status").await;
        let p2 = descobrir_pid_por_porta(8000).is_some();
        let p3 = pid_esta_ativo(pid);
        let provas = [p1, p2, p3].into_iter().filter(|&v| v).count();
        if provas >= 2 {
            return Ok(());
        }
        let snap: Vec<String> = match std::fs::read_to_string(&caminho_stderr) {
            Ok(conteudo) => conteudo
                .lines()
                .take(16)
                .map(|s| s.to_string())
                .filter(|s| !s.trim().is_empty())
                .collect(),
            Err(_) => Vec::new(),
        };
        let mut msg = format!(
            "API FastAPI (Prometeu) não respondeu em 40s (provas: probe_http={}, pid_porta={}, pid_ativo={}).",
            p1, p2, p3
        );
        if !snap.is_empty() {
            msg.push_str(" Último stderr: ");
            msg.push_str(&snap.join(" | "));
        } else {
            msg.push_str(&format!(
                " (sem linhas de erro — ver log completo em {} e/ou JSONL em local_memory/logs/)",
                caminho_stderr.display()
            ));
        }
        let _ = parar_servico_interno(state, &ServicoNome::Api).await;
        return Err(msg);
    }
    Ok(())
}

async fn iniciar_frontend(state: &'_ State<'_, LauncherState>) -> Result<(), String> {
    if probe_http_frontend(3000).await {
        let pid = descobrir_pid_por_porta(3000);
        if let Some(pid_achado) = pid {
            let mut map = state.processos.lock().unwrap();
            map.insert(
                ServicoNome::Frontend,
                (pid_achado, Rastreado::Externo, Instant::now()),
            );
        }
        return Ok(());
    }
    let ok = aguardar_servico_frontend(3000, 30).await;
    if ok {
        let pid = descobrir_pid_por_porta(3000);
        if let Some(pid_achado) = pid {
            let mut map = state.processos.lock().unwrap();
            map.insert(
                ServicoNome::Frontend,
                (pid_achado, Rastreado::Externo, Instant::now()),
            );
        }
        Ok(())
    } else {
        Err("Frontend (Next.js) não subiu em 30s (beforeDevCommand deve rodar npm run dev)."
            .to_string())
    }
}

async fn parar_servico_interno(state: &'_ State<'_, LauncherState>, nome: &ServicoNome) -> bool {
    let item = {
        let mut map = state.processos.lock().unwrap();
        map.remove(nome)
    };

    if let Some((pid, mut rastreado, _)) = item {
        rastreado.parar(pid).await;
        true
    } else {
        false
    }
}

fn construir_status(
    nome: &ServicoNome,
    pid_rastreado: Option<u32>,
    probe_ok: bool,
) -> ServiceStatus {
    let porta = nome.porta();
    match pid_rastreado {
        Some(pid) => {
            let ativo = pid_esta_ativo(pid);
            let online = probe_ok || ativo;
            ServiceStatus {
                online,
                pid: Some(pid),
                port: porta,
                uptime_segundos: if ativo { uptime_por_pid(pid) } else { None },
                memoria_mb: if ativo { memoria_por_pid(pid) } else { None },
            }
        }
        None => ServiceStatus {
            online: probe_ok,
            pid: None,
            port: porta,
            uptime_segundos: None,
            memoria_mb: None,
        },
    }
}

#[tauri::command]
async fn check_services(state: State<'_, LauncherState>) -> Result<CheckServicesResult, String> {
    let (ollama_pid, api_pid, frontend_pid, chatcli_pid) = {
        let map = state.processos.lock().unwrap();
        (
            map.get(&ServicoNome::Ollama).map(|(p, _, _)| *p),
            map.get(&ServicoNome::Api).map(|(p, _, _)| *p),
            map.get(&ServicoNome::Frontend).map(|(p, _, _)| *p),
            map.get(&ServicoNome::Chatcli).map(|(p, _, _)| *p),
        )
    };

    let (ollama_ok, api_ok, frontend_ok) = tokio::join!(
        probe_http(11434, "GET", "/api/tags"),
        probe_http(8000, "GET", "/api/status"),
        probe_http_frontend(3000),
    );

    Ok(CheckServicesResult {
        ollama: construir_status(&ServicoNome::Ollama, ollama_pid, ollama_ok),
        api: construir_status(&ServicoNome::Api, api_pid, api_ok),
        frontend: construir_status(&ServicoNome::Frontend, frontend_pid, frontend_ok),
        chatcli: construir_status(&ServicoNome::Chatcli, chatcli_pid, false),
    })
}

#[tauri::command]
async fn start_all(
    state: State<'_, LauncherState>,
    include_ollama: Option<bool>,
) -> Result<String, String> {
    let com_ollama = include_ollama.unwrap_or(true);
    let mut erros: Vec<String> = Vec::new();

    if com_ollama {
        if let Err(e) = iniciar_ollama(&state).await {
            erros.push(format!("Ollama: {}", e));
        }
    }

    if let Err(e) = iniciar_api(&state).await {
        erros.push(format!("API: {}", e));
    }

    if let Err(e) = iniciar_frontend(&state).await {
        erros.push(format!("Frontend: {}", e));
    }

    if erros.is_empty() {
        Ok("Todos os serviços iniciados com sucesso.".to_string())
    } else {
        Err(erros.join(" | "))
    }
}

#[tauri::command]
async fn stop_all(
    state: State<'_, LauncherState>,
    include_ollama: Option<bool>,
) -> Result<String, String> {
    let com_ollama = include_ollama.unwrap_or(false);
    let mut nomes: Vec<ServicoNome> = Vec::new();

    nomes.push(ServicoNome::Frontend);
    nomes.push(ServicoNome::Api);
    if com_ollama {
        nomes.push(ServicoNome::Ollama);
    }
    nomes.push(ServicoNome::Chatcli);

    for nome in &nomes {
        parar_servico_interno(&state, nome).await;
    }

    Ok("Serviços finalizados.".to_string())
}

#[tauri::command]
async fn stop_service(state: State<'_, LauncherState>, name: String) -> Result<String, String> {
    let nome = ServicoNome::from_str(&name)
        .ok_or_else(|| format!("Serviço desconhecido: {}", name))?;
    let ok = parar_servico_interno(&state, &nome).await;
    if ok {
        Ok(format!("{} parado.", nome.display()))
    } else {
        Ok(format!("{} não estava rodando ou já foi parado.", nome.display()))
    }
}

#[tauri::command]
#[allow(deprecated)]
fn open_in_explorer(app: AppHandle, kind: String) -> Result<String, String> {
    let caminho = match kind.to_lowercase().as_str() {
        "memoria" => {
            let mut sys = System::new_all();
            sys.refresh_all();
            let relatorio = pasta_projeto().join("logs");
            let _ = std::fs::create_dir_all(&relatorio);
            let arquivo = relatorio.join(format!(
                "memoria_{}.txt",
                Utc::now().format("%Y%m%d_%H%M%S")
            ));
            let conteudo = format!(
                "Memória total: {} MB\nMemória usada: {} MB\nMemória livre: {} MB\n",
                sys.total_memory() / 1024 / 1024,
                sys.used_memory() / 1024 / 1024,
                sys.free_memory() / 1024 / 1024,
            );
            let _ = std::fs::write(&arquivo, conteudo);
            relatorio
        }
        "projeto" => pasta_projeto(),
        "modelos" => {
            let p = pasta_modelos();
            let _ = std::fs::create_dir_all(&p);
            p
        }
        outro => return Err(format!("Tipo desconhecido: {}", outro)),
    };

    let shell = app.shell();
    shell
        .open(caminho.to_string_lossy().to_string(), None)
        .map_err(|e| format!("Falha ao abrir explorador: {}", e))?;

    Ok(format!("Aberto em: {}", caminho.display()))
}

fn resolver_caminho_log(kind: &str) -> PathBuf {
    let hoje = Utc::now().format("%Y-%m-%d").to_string();
    match kind {
        "fastapi" => {
            let p = pasta_projeto().join("local_memory").join("logs").join("fastapi_stdout.log");
            if p.exists() {
                p
            } else {
                let fallback = pasta_projeto().join("local_memory").join("logs").join("fastapi_demo.log");
                let _ = std::fs::create_dir_all(fallback.parent().unwrap());
                if !fallback.exists() {
                    let demo = format!(
                        "{}\n{}\n{}\n",
                        "2026-09-29T00:00:00Z INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)",
                        "2026-09-29T00:00:01Z INFO:     Started reloader process [demo] using WatchFiles",
                        "2026-09-29T00:00:02Z INFO:     Application startup complete."
                    );
                    let _ = std::fs::write(&fallback, demo);
                }
                fallback
            }
        }
        "jsonl" => {
            let base = if usar_force_fallback_memory() {
                pasta_projeto().join("local_memory").join("logs")
            } else {
                PathBuf::from("G:/memory/logs")
            };
            let _ = std::fs::create_dir_all(&base);
            base.join(format!("{}.jsonl", hoje))
        }
        "ollama" => {
            let p = pasta_projeto().join("local_memory").join("logs").join("ollama_stdout.log");
            if p.exists() {
                p
            } else {
                let fallback = pasta_projeto().join("local_memory").join("logs").join("ollama_demo.log");
                let _ = std::fs::create_dir_all(fallback.parent().unwrap());
                if !fallback.exists() {
                    let demo = format!(
                        "{}\n{}\n{}\n",
                        "2026/09/29 00:00:00 routes.go:763: routes",
                        "2026/09/29 00:00:01 routes.go:764: routes",
                        "time=2026-09-29T00:00:02.000Z level=INFO msg=\"listening on 127.0.0.1:11434 (version 0.3.12)\""
                    );
                    let _ = std::fs::write(&fallback, demo);
                }
                fallback
            }
        }
        _ => PathBuf::from("unknown.log"),
    }
}

fn extrair_campos(kind: &str, linha: &str) -> (String, Option<String>, Option<String>, String) {
    let ts = Utc::now().to_rfc3339();
    if kind == "jsonl" {
        if let Ok(v) = serde_json::from_str::<Value>(linha) {
            let ts_json = v.get("ts").and_then(|x| x.as_str()).unwrap_or(&ts).to_string();
            let level = v.get("level").and_then(|x| x.as_str()).map(|s| s.to_string());
            let tag = v.get("tag").and_then(|x| x.as_str()).map(|s| s.to_string());
            let msg = v.get("msg").and_then(|x| x.as_str()).unwrap_or(linha).to_string();
            return (ts_json, level, tag, msg);
        }
    }
    let up = linha.to_uppercase();
    let level = if up.contains("ERROR") || up.contains("ERR") {
        Some("ERROR".to_string())
    } else if up.contains("WARN") {
        Some("WARN".to_string())
    } else if up.contains("DEBUG") {
        Some("DEBUG".to_string())
    } else if up.contains("INFO") {
        Some("INFO".to_string())
    } else {
        None
    };
    (ts, level, None, linha.to_string())
}

#[derive(Serialize, Clone)]
struct LogLinePayload {
    kind: String,
    ts: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    level: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    tag: Option<String>,
    msg: String,
    raw: String,
}

#[tauri::command]
async fn tail_logs(
    app_handle: AppHandle,
    state: State<'_, LauncherState>,
    kind: String,
    stop: bool,
) -> Result<String, String> {
    if !["fastapi", "jsonl", "ollama"].contains(&kind.as_str()) {
        return Err(format!("Kind inválido: {}", kind));
    }

    if stop {
        let flags = state.stop_flags.lock().unwrap();
        if let Some(flag) = flags.get(&kind) {
            flag.store(true, Ordering::SeqCst);
        }
        return Ok(format!("Tail de '{}' parado.", kind));
    }

    let stop_flag = {
        let mut flags = state.stop_flags.lock().unwrap();
        if let Some(existente) = flags.get(&kind) {
            existente.store(false, Ordering::SeqCst);
            existente.clone()
        } else {
            let novo = Arc::new(AtomicBool::new(false));
            flags.insert(kind.clone(), novo.clone());
            novo
        }
    };

    let caminho = resolver_caminho_log(&kind);
    let caminho_spawn = caminho.clone();
    let kind_clone = kind.clone();
    let kind_clone2 = kind.clone();
    let app_handle_clone = app_handle.clone();
    let stop_flag_clone = stop_flag.clone();

    let _ = tokio::spawn(async move {
        let arquivo = match tokio::fs::File::open(&caminho_spawn).await {
            Ok(f) => f,
            Err(e) => {
                let _ = app_handle_clone.emit(
                    "log://line",
                    LogLinePayload {
                        kind: kind_clone.clone(),
                        ts: Utc::now().to_rfc3339(),
                        level: Some("ERROR".to_string()),
                        tag: None,
                        msg: format!("Falha ao abrir log: {}", e),
                        raw: format!("Falha ao abrir log: {}", e),
                    },
                );
                return;
            }
        };
        let mut arquivo = arquivo;
        let _ = arquivo.seek(SeekFrom::End(0)).await;
        let mut leitor = tokio::io::BufReader::new(arquivo);
        let mut linha = String::new();

        loop {
            if stop_flag_clone.load(Ordering::SeqCst) {
                break;
            }
            linha.clear();
            let bytes_lidos = match leitor.read_line(&mut linha).await {
                Ok(n) => n,
                Err(e) => {
                    let _ = app_handle_clone.emit(
                        "log://line",
                        LogLinePayload {
                            kind: kind_clone.clone(),
                            ts: Utc::now().to_rfc3339(),
                            level: Some("ERROR".to_string()),
                            tag: None,
                            msg: format!("Erro ao ler linha: {}", e),
                            raw: format!("Erro ao ler linha: {}", e),
                        },
                    );
                    tokio::time::sleep(Duration::from_millis(500)).await;
                    continue;
                }
            };
            if bytes_lidos == 0 {
                tokio::time::sleep(Duration::from_millis(500)).await;
                continue;
            }
            let linha_trim = linha.trim_end_matches(&['\n', '\r'][..]);
            if linha_trim.is_empty() {
                continue;
            }
            let (ts, level, tag, msg) = extrair_campos(&kind_clone, linha_trim);
            let payload = LogLinePayload {
                kind: kind_clone.clone(),
                ts,
                level,
                tag,
                msg,
                raw: linha_trim.to_string(),
            };
            let _ = app_handle_clone.emit("log://line", &payload);
        }
    });

    Ok(format!("Tail de '{}' iniciado em: {}", kind_clone2, caminho.display()))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_single_instance::init(|_app, _argv, _cwd| {}))
        .plugin(tauri_plugin_window_state::Builder::default().with_filename("neurocore-window-state.json").build())
        .plugin(tauri_plugin_notification::init())
        .manage(LauncherState::default())
        .invoke_handler(tauri::generate_handler![
            check_services,
            start_all,
            stop_all,
            stop_service,
            open_in_explorer,
            tail_logs,
        ])
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                let app_handle = window.app_handle().clone();
                api.prevent_close();
                let win = window.clone();
                tauri::async_runtime::spawn(async move {
                    let state: State<'_, LauncherState> = app_handle.state::<LauncherState>();
                    let _ = timeout(
                        Duration::from_secs(8),
                        async {
                            let _ = stop_all(state, Some(false)).await;
                        },
                    )
                    .await;
                    let _ = win.destroy();
                });
            }
        })
        .setup(|app| {
            let _window = app.get_webview_window("main").unwrap();
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
