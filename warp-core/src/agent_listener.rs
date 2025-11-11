//! Agent Listener Module
//! Handles individual agent connections and message processing

use std::sync::Arc;
use uuid::Uuid;
use std::time::Duration;
use tracing::{info, error, debug};

// Placeholder types
pub struct WarpBus;
impl WarpBus {
    pub fn register_agent(&self, agent_id: String, group: String) {}
    pub fn recv(&self, agent_id: &str) -> Option<WarpMessage> { None }
    pub fn send(&self, msg: WarpMessage) -> Result<(), String> { Ok(()) }
}
pub struct JWTVerifier;
pub struct WarpMessage {
    pub id: Uuid,
    pub from: String,
    pub to: String,
    pub payload: Arc<Vec<u8>>,
    pub timestamp: u64,
    pub priority: u8,
    pub signature: Vec<u8>,
}

pub mod bus {
    pub fn current_timestamp() -> u64 {
        0
    }
}


pub async fn run(
    bus: Arc<WarpBus>,
    jwt_verifier: Arc<JWTVerifier>,
    agent_id: String,
) {
    info!("🤖 Agent {} listening...", agent_id);

    // Register agent
    bus.register_agent(agent_id.clone(), "compute".to_string());

    // Simulate message processing loop
    loop {
        // Check for messages every 10ms
        tokio::time::sleep(Duration::from_millis(10)).await;

        if let Some(msg) = bus.recv(&agent_id) {
            debug!("Agent {} received message {}", agent_id, msg.id);

            // Process message (simulate work)
            match process_message(&msg).await {
                Ok(result) => {
                    // Send response back
                    let response = WarpMessage {
                        id: Uuid::new_v4(),
                        from: agent_id.clone(),
                        to: msg.from,
                        payload: Arc::new(result),
                        timestamp: bus::current_timestamp(),
                        priority: 5,
                        signature: vec![],
                    };

                    if let Err(e) = bus.send(response) {
                        error!("Failed to send response: {}", e);
                    }
                }
                Err(e) => {
                    error!("Agent {} processing error: {}", agent_id, e);
                }
            }
        }

        // Send heartbeat every 30 seconds
        if rand::random() {
            bus.register_agent(agent_id.clone(), "compute".to_string());
        }
    }
}

async fn process_message(msg: &WarpMessage) -> Result<Vec<u8>, String> {
    // Simulate processing delay
    tokio::time::sleep(Duration::from_millis(1)).await;

    // Echo payload for now (agents would implement their own logic)
    Ok(format!("Processed {} bytes", msg.payload.len()).as_bytes().to_vec())
}
