# Build stage
FROM rust:1.78 as builder

WORKDIR /usr/src/warp-core
COPY . .
RUN cargo build --release

# Runtime stage
FROM debian:buster-slim
COPY --from=builder /usr/src/warp-core/target/release/warp-core /usr/local/bin/warp-core
CMD ["warp-core"]
