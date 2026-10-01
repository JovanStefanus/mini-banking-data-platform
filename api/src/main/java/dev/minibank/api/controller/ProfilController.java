package dev.minibank.api.controller;

import dev.minibank.api.error.NotFoundException;
import dev.minibank.api.model.ProfilNasabah;
import dev.minibank.api.repository.ProfilRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Master Data Management: profil 360 nasabah (golden record dari tiga sumber). */
@RestController
@RequestMapping("/api/v1/nasabah")
public class ProfilController {
    private final ProfilRepository repository;

    public ProfilController(ProfilRepository repository) {
        this.repository = repository;
    }

    @GetMapping("/{id}/profil")
    public ProfilNasabah profil(@PathVariable int id) {
        return repository.findById(id)
                .orElseThrow(() -> new NotFoundException("Nasabah dengan id " + id + " tidak ditemukan"));
    }
}
