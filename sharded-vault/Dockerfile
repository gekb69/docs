# Build stage
FROM rust:1.78 as builder

WORKDIR /usr/src/sharded-vault
COPY . .
RUN cargo build --release

# Runtime stage
FROM debian:buster-slim
COPY --from=builder /usr/src/sharded-vault/target/release/sharded-vault /usr/local/bin/sharded-vault
CMD ["sharded-vault"]
