use async_trait::async_trait;
use aws_sdk_s3::Client as S3Client;
use axum::extract::{Path, State};
use axum::response::Json;
use serde_json::{json, Value};
use std::error;
use std::sync::Arc;
use tokio_stream::StreamExt;

#[derive(Clone)]
pub struct AppState {
    pub s3client: S3Client,
}

// You need to define a trait, that can then be implemented for an outside type
#[async_trait]
pub trait GetFile {
    async fn get_subject(&self, url: String) -> Result<Value, Box<dyn error::Error>>;
}

#[async_trait]
impl GetFile for S3Client {
    async fn get_subject(&self, subject: String) -> Result<Value, Box<dyn error::Error>> {
        println!("get_subject '{}'", subject);
        let key = format!("mainnet/mappings/{}.json", subject);
        tracing::debug!("Key '{}'", &key);

        let result = self
            .get_object()
            .bucket("offchain-metadata-bucket-4xy2")
            .key(key)
            .send()
            .await;
        let mut subject_string = String::new();

        match result {
            Ok(mut result) => {
                println!("Result {:?}", result);
                // Reading from a ByteStream: https://docs.rs/aws-sdk-s3/latest/aws_sdk_s3/primitives/struct.ByteStream.html
                /*
                let subject_bytes = &result.body().collect().await.map(|data| data.into_bytes());
                match subject_bytes {
                    Ok(b) => println!("{:?}", b),
                    Err(e) => println!("{:?}", e)
                }
                */
                while let Some(bytes) = result.body.try_next().await? {
                    if let Ok(tmp_string) = String::from_utf8(bytes.to_vec()) {
                        subject_string.push_str(&tmp_string);
                    }
                }
            }
            Err(e) => {
                // You must return the error here!
                // Or else the empty subject_value will be returned!
                println!("Error {}", &e.into_service_error());
            }
        }
        // subject_value = Value::from(subject_string);

        let subject_value = serde_json::from_str(&subject_string).unwrap();
        Ok(subject_value)
    }
}

pub async fn root() -> Json<Value> {
    Json(json!({ "msg": "I am GET /" }))
}

pub async fn get_metadata(
    Path(subject): Path<String>,
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    println!("Metadata Called with {}", subject);
    let msg = format!("I am GET /metadata/{}", subject);
    // 00000002df633853f6a47465c9496721d2d5b1291b8398016c0e87ae6e7574636f696e
    if let Ok(subject) = state.s3client.get_subject(subject).await {
        println!("{}", subject);

        // Json(json!({ "msg": msg, "foo": "bar" }))
        Json(subject)
    } else {
        Json(json!({ "msg": msg, "foo": "bar" }))
    }
}

pub async fn get_metadata_properties(Path(subject): Path<String>) -> Json<Value> {
    let msg = format!("I am GET /metadata/{}/properties", subject);
    Json(json!({ "msg": msg }))
}

pub async fn get_single_metadata_propertie(
    Path((subject, name)): Path<(String, String)>,
) -> Json<Value> {
    tracing::info!("Metadata Called with {}", name);
    let msg = format!("I am GET /metadata/{}/properties/{}", subject, name);
    Json(json!({ "msg": msg }))
}

pub async fn post_query() -> Json<Value> {
    Json(json!({ "msg": "You poste a query" }))
}
