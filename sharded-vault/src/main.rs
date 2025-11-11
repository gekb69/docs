mod shard;
use shard::VaultShard;
use clap::Parser;
use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tracing::{info, error, debug};
use std::sync::Arc;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(author, version, about = "Sharded Vault Server")]
struct Args {
#[arg(short, long, env = "VAULT_SHARD_ID")]
shard_id: u8,
#[arg(short, long, env = "VAULT_THRESHOLD")]
threshold: u8,
#[arg(short, long, env = "VAULT_SHARDS")]
total_shares: u8,
#[arg(short, long, env = "VAULT_STORAGE", default_value = "./shards")]
storage: PathBuf,
#[arg(short, long, default_value = "9000")]
port: u16,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
tracing_subscriber::fmt().with_env_filter("info,sharded_vault=debug").json().init();

let args = Args::parse();
let shard = Arc::new(tokio::sync::Mutex::new(
VaultShard::new(args.shard_id, args.threshold, args.total_shares, args.storage.clone()).unwrap()
));

let addr = format!("0.0.0.0:{}", args.port);
let listener = TcpListener::bind(&addr).await?;

info!("🔐 Vault Shard {}/{} listening on {}", args.shard_id, args.total_shares, addr);
info!("📂 Storage: {:?}", args.storage);
info!("🔑 Threshold: {}", args.threshold);

loop {
let (socket, _) = listener.accept().await?;
let shard_clone = shard.clone();
tokio::spawn(async move {
if let Err(e) = handle_client(socket, shard_clone).await {
error!("Client error: {}", e);
}
});
}
}

async fn handle_client(
mut socket: TcpStream,
shard: Arc<tokio::sync::Mutex<VaultShard>>
) -> Result<(), Box<dyn std::error::Error>> {
let mut buffer = vec![0u8; 4096];

// Read command
let n = socket.read(&mut buffer).await?;
if n == 0 {
return Ok(());
}

let command = String::from_utf8_lossy(&buffer[..n]);
let parts: Vec<&str> = command.trim().split_whitespace().collect();

if parts.is_empty() {
socket.write_all(b"ERR: Empty command\n").await?;
return Ok(());
}

match parts[0] {
"STORE" if parts.len() == 3 => {
let key = parts[1];
let secret = parts[2].as_bytes();

let mut shard_lock = shard.lock().await;
match shard_lock.store_secret(key, secret) {
Ok(_) => {
socket.write_all(b"OK: Secret stored\n").await?;
}
Err(e) => {
socket.write_all(format!("ERR: {}\n", e).as_bytes()).await?;
}
}
}

"GET" if parts.len() == 2 => {
let key = parts[1];

let shard_lock = shard.lock().await;
match shard_lock.get_share(key) {
Ok(share) => {
socket.write_all(share.as_slice()).await?;
socket.write_all(b"\n").await?;
}
Err(e) => {
socket.write_all(format!("ERR: {}\n", e).as_bytes()).await?;
}
}
}

"STATUS" => {
let shard_lock = shard.lock().await;
let status = format!(
"Shard: {}/{}\nThreshold: {}\nKeys: {}\n",
shard_lock.id,
shard_lock.total_shares,
shard_lock.threshold,
shard_lock.cache.len()
);
socket.write_all(status.as_bytes()).await?;
}

_ => {
socket.write_all(b"ERR: Invalid command\n").await?;
}
}

Ok(())
}
