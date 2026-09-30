package dev.minibank.api.controller;

import dev.minibank.api.error.BadRequestException;
import dev.minibank.api.model.ApiModels.PageResponse;
import dev.minibank.api.model.ApiModels.Transaksi;
import dev.minibank.api.repository.TransaksiRepository;
import java.time.LocalDate;
import java.util.Locale;
import java.util.Set;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/transaksi")
public class TransaksiController {
    private static final Set<String> CHANNELS = Set.of("ATM", "MOBILE", "INTERNET", "TELLER");
    private static final int MAX_SIZE = 200;

    private final TransaksiRepository repository;

    public TransaksiController(TransaksiRepository repository) {
        this.repository = repository;
    }

    @GetMapping
    public PageResponse<Transaksi> list(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate tanggal,
            @RequestParam(required = false) String channel,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {

        if (page < 0) {
            throw new BadRequestException("page tidak boleh negatif");
        }
        if (size < 1 || size > MAX_SIZE) {
            throw new BadRequestException("size harus antara 1 dan " + MAX_SIZE);
        }
        String channelFilter = null;
        if (channel != null && !channel.isBlank()) {
            channelFilter = channel.trim().toUpperCase(Locale.ROOT);
            if (!CHANNELS.contains(channelFilter)) {
                throw new BadRequestException("channel harus salah satu dari " + CHANNELS);
            }
        }

        long total = repository.count(tanggal, channelFilter);
        int totalPages = (int) Math.ceil((double) total / size);
        var data = repository.find(tanggal, channelFilter, size, (long) page * size);
        return new PageResponse<>(page, size, total, totalPages, data);
    }
}
