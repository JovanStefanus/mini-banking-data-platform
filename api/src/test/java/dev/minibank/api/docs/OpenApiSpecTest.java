package dev.minibank.api.docs;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Menjaga dokumentasi OpenAPI (ditulis manual) tidak ketinggalan dari endpoint yang ada. */
class OpenApiSpecTest {
    private static final List<String> ENDPOINT = List.of(
            "/api/v1/transaksi:",
            "/api/v1/nasabah/{id}:",
            "/api/v1/nasabah/{id}/riwayat:",
            "/api/v1/nasabah/{id}/profil:",
            "/api/v1/ringkasan/harian:",
            "/actuator/health:");

    @Test
    void semuaEndpointTercatatDiOpenApi() throws IOException {
        try (InputStream in = getClass().getResourceAsStream("/static/openapi.yaml")) {
            assertThat(in).as("file static/openapi.yaml harus ada").isNotNull();
            String yaml = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            for (String endpoint : ENDPOINT) {
                assertThat(yaml).as("endpoint " + endpoint).contains(endpoint);
            }
        }
    }
}
