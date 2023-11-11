//! This is an example function that leverages the Lambda Rust runtime's HTTP support
//! and the [axum](https://docs.rs/axum/latest/axum/index.html) web framework.  The
//! runtime HTTP support is backed by the [tower::Service](https://docs.rs/tower-service/0.3.2/tower_service/trait.Service.html)
//! trait.  Axum applications are also backed by the `tower::Service` trait.  That means
//! that it is fairly easy to build an Axum application and pass the resulting `Service`
//! implementation to the Lambda runtime to run as a Lambda function.  By using Axum instead
//! of a basic `tower::Service` you get web framework niceties like routing, request component
//! extraction, validation, etc.

use axum::{
    routing::{get, post},
    Router,
};
use lambda_http::{run, Error};
use std::sync::Arc;

pub mod handlers;

#[tokio::main]
async fn main() -> Result<(), Error> {
    let config = aws_config::load_from_env().await;
    let s3client = aws_sdk_s3::Client::new(&config);

    println!(" What?! ");
    let app_state = Arc::new(handlers::AppState { s3client });

    // enable CloudWatch error logging by the runtime
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        // disable printing the name of the module in every log line.
        .with_target(false)
        // disabling time is handy because CloudWatch will add the ingestion time.
        .without_time()
        .init();

    /*
        GET  /metadata/{subject}
        GET  /metadata/{subject}/properties
        GET  /metadata/{subject}/properties/{name}
        POST /metadata/query
    */
    let app = Router::new()
        .route("/", get(handlers::root))
        .route("/metadata/:subject", get(handlers::get_metadata))
        .route(
            "/metadata/:subject/properties",
            get(handlers::get_metadata_properties),
        )
        .route(
            "/metadata/:subject/properties/:name",
            get(handlers::get_single_metadata_propertie),
        )
        .route("/metadata/query", post(handlers::post_query))
        .with_state(app_state);

    println!("Starting new run with app");
    run(app).await

}
