package dev.minibank.api.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import dev.minibank.api.error.BadRequestException;
import dev.minibank.api.model.ApiModels.PageResponse;
import dev.minibank.api.model.ApiModels.Transaksi;
import dev.minibank.api.repository.TransaksiRepository;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.Test;

class TransaksiControllerTest {
    private final TransaksiRepository repository = mock(TransaksiRepository.class);
    private final TransaksiController controller = new TransaksiController(repository);
    private final LocalDate tanggal = LocalDate.of(2026, 9, 1);

    @Test
    void ukuranHalamanTerlaluBesarDitolak() {
        assertThatThrownBy(() -> controller.list(tanggal, null, 0, 201))
                .isInstanceOf(BadRequestException.class)
                .hasMessageContaining("size");
    }

    @Test
    void ukuranHalamanNolDitolak() {
        assertThatThrownBy(() -> controller.list(tanggal, null, 0, 0))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    void halamanNegatifDitolak() {
        assertThatThrownBy(() -> controller.list(tanggal, null, -1, 50))
                .isInstanceOf(BadRequestException.class)
                .hasMessageContaining("page");
    }

    @Test
    void channelTidakDikenalDitolak() {
        assertThatThrownBy(() -> controller.list(tanggal, "WA", 0, 50))
                .isInstanceOf(BadRequestException.class)
                .hasMessageContaining("channel");
    }

    @Test
    void channelDinormalisasiKeHurufBesar() {
        controller.list(tanggal, " mobile ", 0, 50);
        verify(repository).count(tanggal, "MOBILE");
    }

    @Test
    void channelKosongDiabaikan() {
        controller.list(tanggal, "   ", 0, 50);
        verify(repository).count(tanggal, null);
    }

    @Test
    void totalHalamanDibulatkanKeAtas() {
        when(repository.count(tanggal, null)).thenReturn(218L);
        PageResponse<Transaksi> hasil = controller.list(tanggal, null, 0, 5);
        assertThat(hasil.totalElements()).isEqualTo(218L);
        assertThat(hasil.totalPages()).isEqualTo(44);
    }

    @Test
    void tanpaDataTotalHalamanNol() {
        when(repository.count(tanggal, null)).thenReturn(0L);
        when(repository.find(tanggal, null, 50, 0L)).thenReturn(List.of());
        PageResponse<Transaksi> hasil = controller.list(tanggal, null, 0, 50);
        assertThat(hasil.totalPages()).isZero();
        assertThat(hasil.data()).isEmpty();
    }

    @Test
    void offsetDihitungDariNomorHalaman() {
        controller.list(tanggal, null, 2, 5);
        verify(repository).find(tanggal, null, 5, 10L);
    }
}
