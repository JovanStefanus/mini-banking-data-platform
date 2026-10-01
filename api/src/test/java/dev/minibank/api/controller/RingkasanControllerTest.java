package dev.minibank.api.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

import dev.minibank.api.error.BadRequestException;
import dev.minibank.api.repository.RingkasanRepository;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

class RingkasanControllerTest {
    private final RingkasanRepository repository = mock(RingkasanRepository.class);
    private final RingkasanController controller = new RingkasanController(repository);

    @Test
    void dariSetelahSampaiDitolak() {
        assertThatThrownBy(() -> controller.harian(LocalDate.of(2026, 9, 10), LocalDate.of(2026, 9, 1)))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    void rentangLebihDari366HariDitolak() {
        assertThatThrownBy(() -> controller.harian(LocalDate.of(2024, 1, 1), LocalDate.of(2026, 1, 1)))
                .isInstanceOf(BadRequestException.class)
                .hasMessageContaining("366");
    }

    @Test
    void rentangTepat366HariDiterima() {
        LocalDate sampai = LocalDate.of(2026, 9, 1);
        LocalDate dari = sampai.minusDays(366);
        controller.harian(dari, sampai);
        verify(repository).harian(dari, sampai);
    }

    @Test
    void tanpaParameterMemakai30HariTerakhir() {
        controller.harian(null, null);
        ArgumentCaptor<LocalDate> dari = ArgumentCaptor.forClass(LocalDate.class);
        ArgumentCaptor<LocalDate> sampai = ArgumentCaptor.forClass(LocalDate.class);
        verify(repository).harian(dari.capture(), sampai.capture());
        assertThat(ChronoUnit.DAYS.between(dari.getValue(), sampai.getValue())).isEqualTo(29);
    }
}
