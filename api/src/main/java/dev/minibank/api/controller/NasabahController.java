package dev.minibank.api.controller;

import dev.minibank.api.error.NotFoundException;
import dev.minibank.api.model.ApiModels.Nasabah;
import dev.minibank.api.model.ApiModels.NasabahVersi;
import dev.minibank.api.repository.NasabahRepository;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Master data nasabah dari dim_nasabah. */
@RestController
@RequestMapping("/api/v1/nasabah")
public class NasabahController {
    private final NasabahRepository repository;

    public NasabahController(NasabahRepository repository) {
        this.repository = repository;
    }

    @GetMapping("/{id}")
    public Nasabah get(@PathVariable int id) {
        return repository.findCurrent(id)
                .orElseThrow(() -> new NotFoundException("Nasabah dengan id " + id + " tidak ditemukan"));
    }

    @GetMapping("/{id}/riwayat")
    public List<NasabahVersi> riwayat(@PathVariable int id) {
        List<NasabahVersi> versi = repository.riwayat(id);
        if (versi.isEmpty()) {
            throw new NotFoundException("Nasabah dengan id " + id + " tidak ditemukan");
        }
        return versi;
    }
}
