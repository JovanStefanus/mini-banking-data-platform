package dev.minibank.api.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import dev.minibank.api.error.NotFoundException;
import dev.minibank.api.model.ApiModels.Nasabah;
import dev.minibank.api.model.ApiModels.NasabahVersi;
import dev.minibank.api.repository.NasabahRepository;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;

class NasabahControllerTest {
    private final NasabahRepository repository = mock(NasabahRepository.class);
    private final NasabahController controller = new NasabahController(repository);

    @Test
    void nasabahDitemukan() {
        Nasabah nasabah = new Nasabah(1, "Budi", "Bandung", "RITEL", LocalDate.of(2024, 1, 1));
        when(repository.findCurrent(1)).thenReturn(Optional.of(nasabah));
        assertThat(controller.get(1)).isEqualTo(nasabah);
    }

    @Test
    void nasabahTidakAdaMenghasilkanNotFound() {
        when(repository.findCurrent(99)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> controller.get(99))
                .isInstanceOf(NotFoundException.class)
                .hasMessageContaining("99");
    }

    @Test
    void riwayatKosongMenghasilkanNotFound() {
        when(repository.riwayat(99)).thenReturn(List.of());
        assertThatThrownBy(() -> controller.riwayat(99)).isInstanceOf(NotFoundException.class);
    }

    @Test
    void riwayatDikembalikanApaAdanya() {
        NasabahVersi versi = new NasabahVersi("Budi", "Bandung", "RITEL",
                LocalDateTime.of(2024, 1, 1, 0, 0), null, true);
        when(repository.riwayat(1)).thenReturn(List.of(versi));
        assertThat(controller.riwayat(1)).containsExactly(versi);
    }
}
