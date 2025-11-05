// crypto_stub.h
#pragma once
#include <stdint.h>
#include <stddef.h>

/*
 * Crypto abstraction layer (stubs).
 * Replace implementations in crypto_stub.c with mbedTLS / tinycrypt equivalents.
 *
 * Design:
 *  - AES streaming: caller initializes AES_CTX via aes_init(key, iv)
 *    then repeatedly calls aes_encrypt_stream(outbuf, inbuf, inlen, &outlen)
 *    finally calls aes_free_ctx().
 *  - SHA-256 streaming: sha256_init(ctx), sha256_update(ctx, data, len), sha256_final(ctx, out32)
 *
 * NOTE: current stub uses very small placeholder implementations to compile.
 */

#define AES_KEY_LEN 32
#define AES_IV_LEN 16
#define SHA256_DIGEST_LEN 32

typedef struct {
    // opaque; replace with mbedtls_aes_context or similar
    uint8_t key[AES_KEY_LEN];
    uint8_t iv[AES_IV_LEN];
} AES_CTX;

typedef struct {
    // simple placeholder; replace with real sha256 context
    uint32_t state[8];
    uint64_t bitlen;
    uint8_t buffer[64];
    size_t buf_idx;
} SHA256_CTX;

// AES
int aes_init(AES_CTX *ctx, const uint8_t *key, size_t keylen, const uint8_t *iv, size_t ivlen);
int aes_encrypt_stream(AES_CTX *ctx, const uint8_t *in, size_t in_len, uint8_t *out, size_t *out_len);
void aes_free(AES_CTX *ctx);

// SHA-256
void sha256_init(SHA256_CTX *ctx);
void sha256_update(SHA256_CTX *ctx, const uint8_t *data, size_t len);
void sha256_final(SHA256_CTX *ctx, uint8_t out_hash[SHA256_DIGEST_LEN]);

// helpers
void bytes_to_hex(const uint8_t *in, size_t in_len, char *out_hex); // out_hex must be 2*in_len+1

