package dev.minibank.api.error;

import static org.assertj.core.api.Assertions.assertThat;

import dev.minibank.api.model.ApiModels.ErrorResponse;
import org.junit.jupiter.api.Test;
import org.springframework.http.ResponseEntity;

class ApiExceptionHandlerTest {
    private final ApiExceptionHandler handler = new ApiExceptionHandler();

    @Test
    void badRequestMenghasilkan400DenganPesan() {
        ResponseEntity<ErrorResponse> hasil = handler.badRequest(new BadRequestException("size tidak valid"));
        assertThat(hasil.getStatusCode().value()).isEqualTo(400);
        assertThat(hasil.getBody().message()).isEqualTo("size tidak valid");
    }

    @Test
    void notFoundMenghasilkan404() {
        ResponseEntity<ErrorResponse> hasil = handler.notFound(new NotFoundException("tidak ada"));
        assertThat(hasil.getStatusCode().value()).isEqualTo(404);
        assertThat(hasil.getBody().status()).isEqualTo(404);
    }

    @Test
    void errorTakTerdugaTidakMembocorkanDetailInternal() {
        ResponseEntity<ErrorResponse> hasil =
                handler.unexpected(new RuntimeException("SELECT * FROM rahasia gagal"));
        assertThat(hasil.getStatusCode().value()).isEqualTo(500);
        assertThat(hasil.getBody().message()).doesNotContain("SELECT");
    }
}
