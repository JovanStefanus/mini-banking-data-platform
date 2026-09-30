package dev.minibank.api.controller;

import dev.minibank.api.error.BadRequestException;
import dev.minibank.api.model.ApiModels.RingkasanHarian;
import dev.minibank.api.repository.RingkasanRepository;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/ringkasan")
public class RingkasanController {
    private static final int MAX_RANGE_DAYS = 366;

    private final RingkasanRepository repository;

    public RingkasanController(RingkasanRepository repository) {
        this.repository = repository;
    }

    /** Tanpa parameter: 30 hari terakhir sampai hari ini. */
    @GetMapping("/harian")
    public List<RingkasanHarian> harian(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dari,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate sampai) {

        LocalDate akhir = sampai != null ? sampai : LocalDate.now();
        LocalDate awal = dari != null ? dari : akhir.minusDays(29);
        if (awal.isAfter(akhir)) {
            throw new BadRequestException("'dari' tidak boleh setelah 'sampai'");
        }
        if (ChronoUnit.DAYS.between(awal, akhir) > MAX_RANGE_DAYS) {
            throw new BadRequestException("Rentang tanggal maksimal " + MAX_RANGE_DAYS + " hari");
        }
        return repository.harian(awal, akhir);
    }
}
