package dev.minibank.api.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import dev.minibank.api.error.NotFoundException;
import dev.minibank.api.model.ProfilNasabah;
import dev.minibank.api.repository.ProfilRepository;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Optional;
import org.junit.jupiter.api.Test;

class ProfilControllerTest {
    private final ProfilRepository repository = mock(ProfilRepository.class);
    private final ProfilController controller = new ProfilController(repository);

    @Test
    void profilDitemukan() {
        ProfilNasabah profil = new ProfilNasabah(1, "Budi", "Bandung", "RITEL", LocalDate.of(2024, 1, 1),
                false, null, null, 3L, new BigDecimal("150000.00"), 0L, null, 0L, 0L, null);
        when(repository.findById(1)).thenReturn(Optional.of(profil));
        assertThat(controller.profil(1)).isEqualTo(profil);
    }

    @Test
    void profilTidakAdaMenghasilkanNotFound() {
        when(repository.findById(99)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> controller.profil(99))
                .isInstanceOf(NotFoundException.class)
                .hasMessageContaining("99");
    }
}
