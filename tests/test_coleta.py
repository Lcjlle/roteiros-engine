"""Testes de `src/coleta.py` (Fase 1 - Coleta).

Nenhum teste aqui bate na rede: `list_channel_videos`, `fetch_via_*` e
`fetch_via_whisperx` sao testados via mock/monkeypatch, cobrindo exatamente
o que a issue #1 pede - parsing do manifesto, a regra de selecao (nao pega
os mais recentes), o fallback legenda->yt-dlp->whisperX, e a limpeza
minima.
"""

import subprocess
import sys
from datetime import UTC, datetime, timedelta

import pytest
from youtube_transcript_api._errors import IpBlocked, TranscriptsDisabled

from src import coleta


def _video(id_, duration=500, views=0, days_ago=0, title="titulo"):
    return {
        "id": id_,
        "title": title,
        "duration": duration,
        "view_count": views,
        "published_at": datetime.now(UTC) - timedelta(days=days_ago),
    }


# --------------------------------------------------------------------------
# Regra de selecao
# --------------------------------------------------------------------------


class TestSelectVideos:
    def test_prefers_best_performers_over_most_recent(self):
        # 5 videos maduros (>6 meses): um antigo e muito visto, quatro
        # recentes (mas ainda maduros) com poucas views.
        videos = [_video("top", views=1_000_000, days_ago=400)]
        videos += [_video(f"recent{i}", views=100, days_ago=190) for i in range(4)]

        selected = coleta.select_videos(videos, target=1)

        assert [v["id"] for v in selected] == ["top"]

    def test_does_not_just_pick_the_30_most_recent(self):
        # 40 videos maduros: os 30 primeiros (mais antigos) tem visualizacoes
        # altas, os 10 mais recentes tem poucas. "os 30 mais recentes"
        # pegaria os 10 de poucas views + 20 dos com muitas; a regra de
        # desempenho deve pegar exatamente os 30 mais vistos.
        old_high_view = [_video(f"old{i}", views=10_000, days_ago=400 + i) for i in range(30)]
        recent_low_view = [_video(f"new{i}", views=10, days_ago=190 + i) for i in range(10)]
        videos = recent_low_view + old_high_view

        selected = coleta.select_videos(videos, target=30)

        assert {v["id"] for v in selected} == {v["id"] for v in old_high_view}
        assert len(selected) == 30

    def test_excludes_shorts_by_duration(self):
        videos = [
            _video("short", duration=45, views=1_000_000, days_ago=400),
            _video("long", duration=500, views=10, days_ago=400),
        ]

        selected = coleta.select_videos(videos, target=1)

        assert [v["id"] for v in selected] == ["long"]

    def test_falls_back_to_whole_pool_when_channel_too_young(self):
        # Canal jovem: nenhum video tem mais de 6 meses. A selecao ainda
        # precisa devolver `target` videos, ranqueados por views - nao os
        # `target` mais recentes.
        videos = [_video(f"v{i}", views=i, days_ago=i) for i in range(1, 6)]

        selected = coleta.select_videos(videos, target=3)

        assert [v["id"] for v in selected] == ["v5", "v4", "v3"]

    def test_unknown_published_at_is_treated_as_recent(self):
        unknown = {
            "id": "unknown",
            "title": "t",
            "duration": 500,
            "view_count": 999,
            "published_at": None,
        }
        mature = _video("mature", views=1, days_ago=400)

        selected = coleta.select_videos([unknown, mature], target=1, min_age_days=182)

        # So "mature" passa no filtro de idade -> pool madura tem 1 video,
        # que e < target(1)? nao, e igual a 1 == target, entao usa a pool
        # madura mesmo com "unknown" tendo mais views.
        assert [v["id"] for v in selected] == ["mature"]


# --------------------------------------------------------------------------
# Fallback legenda -> yt-dlp -> whisperX
# --------------------------------------------------------------------------


class TestCollectTranscriptFallback:
    def test_uses_transcript_api_when_available(self, monkeypatch):
        monkeypatch.setattr(
            coleta,
            "fetch_via_transcript_api",
            lambda vid: [{"start": 0, "duration": 1, "text": "oi"}],
        )
        monkeypatch.setattr(
            coleta, "fetch_via_ytdlp_subs", lambda vid: pytest.fail("nao deveria chamar yt-dlp")
        )
        monkeypatch.setattr(
            coleta, "fetch_via_whisperx", lambda vid: pytest.fail("nao deveria chamar whisperX")
        )

        fragments, source = coleta.collect_transcript("abc")

        assert source == "youtube_transcript_api"
        assert fragments == [{"start": 0, "duration": 1, "text": "oi"}]

    def test_falls_back_to_ytdlp_when_transcript_api_has_nothing(self, monkeypatch):
        monkeypatch.setattr(coleta, "fetch_via_transcript_api", lambda vid: None)
        monkeypatch.setattr(
            coleta, "fetch_via_ytdlp_subs", lambda vid: [{"start": 0, "duration": 1, "text": "oi"}]
        )
        monkeypatch.setattr(
            coleta, "fetch_via_whisperx", lambda vid: pytest.fail("nao deveria chamar whisperX")
        )

        fragments, source = coleta.collect_transcript("abc")

        assert source == "yt-dlp"
        assert fragments == [{"start": 0, "duration": 1, "text": "oi"}]

    def test_falls_back_to_whisperx_only_when_both_legenda_sources_fail(self, monkeypatch):
        calls = []
        monkeypatch.setattr(coleta, "fetch_via_transcript_api", lambda vid: None)
        monkeypatch.setattr(coleta, "fetch_via_ytdlp_subs", lambda vid: None)
        monkeypatch.setattr(
            coleta,
            "fetch_via_whisperx",
            lambda vid: calls.append(vid) or [{"start": 0, "duration": 1, "text": "audio"}],
        )

        fragments, source = coleta.collect_transcript("abc")

        assert source == "whisperx"
        assert calls == ["abc"]
        assert fragments == [{"start": 0, "duration": 1, "text": "audio"}]

    def test_whisperx_without_dependency_raises_clear_error(self, monkeypatch):
        # whisperx e uma dependencia real do projeto (`uv add whisperx`),
        # entao a ausencia so acontece num ambiente quebrado - simula via
        # sys.modules em vez de depender do pacote genuinamente faltando.
        monkeypatch.setitem(sys.modules, "whisperx", None)
        with pytest.raises(RuntimeError, match="whisperX"):
            coleta.fetch_via_whisperx("abc")

    def test_transcript_api_returns_none_only_for_genuinely_missing_captions(self, monkeypatch):
        class FakeApi:
            def fetch(self, video_id):
                raise TranscriptsDisabled(video_id)

        monkeypatch.setattr(coleta, "YouTubeTranscriptApi", FakeApi)

        assert coleta.fetch_via_transcript_api("abc") is None

    def test_transcript_api_reraises_ip_block_instead_of_falling_back(self, monkeypatch):
        # Um IP bloqueado nao e "sem legenda" - nao deve empurrar o video
        # para yt-dlp/whisperX silenciosamente, tem que estourar.
        class FakeApi:
            def fetch(self, video_id):
                raise IpBlocked(video_id)

        monkeypatch.setattr(coleta, "YouTubeTranscriptApi", FakeApi)

        with pytest.raises(IpBlocked):
            coleta.fetch_via_transcript_api("abc")


# --------------------------------------------------------------------------
# Limpeza minima
# --------------------------------------------------------------------------


class TestCleanTranscript:
    def test_removes_music_and_applause_markers(self):
        fragments = [
            {"start": 0.0, "duration": 1.0, "text": "[Music]"},
            {"start": 1.0, "duration": 1.0, "text": "hello there"},
            {"start": 2.0, "duration": 1.0, "text": "[Aplausos]"},
        ]

        trechos = coleta.clean_transcript(fragments)

        assert trechos == [{"inicio_s": 1.0, "texto": "hello there"}]

    def test_joins_adjacent_fragments_into_continuous_text(self):
        fragments = [
            {"start": 0.0, "duration": 2.0, "text": "hello there"},
            {"start": 2.0, "duration": 2.0, "text": "general kenobi"},
        ]

        trechos = coleta.clean_transcript(fragments)

        assert trechos == [{"inicio_s": 0.0, "texto": "hello there general kenobi"}]

    def test_preserves_start_timestamp_of_each_trecho_after_a_gap(self):
        fragments = [
            {"start": 0.0, "duration": 1.0, "text": "primeiro trecho"},
            {"start": 20.0, "duration": 1.0, "text": "segundo trecho"},
        ]

        trechos = coleta.clean_transcript(fragments, gap_threshold=1.0)

        assert trechos == [
            {"inicio_s": 0.0, "texto": "primeiro trecho"},
            {"inicio_s": 20.0, "texto": "segundo trecho"},
        ]

    def test_marker_forces_a_new_trecho_even_without_a_time_gap(self):
        fragments = [
            {"start": 0.0, "duration": 1.0, "text": "antes"},
            {"start": 1.0, "duration": 0.5, "text": "[Music]"},
            {"start": 1.5, "duration": 1.0, "text": "depois"},
        ]

        trechos = coleta.clean_transcript(fragments, gap_threshold=5.0)

        assert trechos == [
            {"inicio_s": 0.0, "texto": "antes"},
            {"inicio_s": 1.5, "texto": "depois"},
        ]

    def test_does_not_touch_punctuation(self):
        fragments = [{"start": 0.0, "duration": 1.0, "text": "sem pontuacao nenhuma aqui"}]

        trechos = coleta.clean_transcript(fragments)

        assert trechos[0]["texto"] == "sem pontuacao nenhuma aqui"

    def test_word_count_counts_words_across_trechos(self):
        trechos = [{"inicio_s": 0.0, "texto": "um dois tres"}, {"inicio_s": 5.0, "texto": "quatro"}]

        assert coleta.word_count(trechos) == 4


# --------------------------------------------------------------------------
# Manifesto
# --------------------------------------------------------------------------


class TestManifesto:
    def test_write_then_read_round_trips(self, tmp_path):
        rows = [
            {
                "id": "abc",
                "titulo": "Titulo A",
                "duracao_s": 500,
                "contagem_palavras": 1000,
                "fonte": "legenda",
            },
            {
                "id": "def",
                "titulo": "Titulo B",
                "duracao_s": 300,
                "contagem_palavras": 600,
                "fonte": "whisperX",
            },
        ]
        path = tmp_path / "manifesto.csv"

        coleta.write_manifesto(rows, path)
        read_rows = coleta.read_manifesto(path)

        assert len(read_rows) == 2
        assert read_rows[0]["id"] == "abc"
        assert read_rows[0]["titulo"] == "Titulo A"
        assert read_rows[0]["fonte"] == "legenda"
        assert read_rows[1]["fonte"] == "whisperX"

    def test_write_creates_parent_directory(self, tmp_path):
        path = tmp_path / "nested" / "manifesto.csv"
        coleta.write_manifesto([], path)
        assert path.exists()


# --------------------------------------------------------------------------
# Portao da Fase 1
# --------------------------------------------------------------------------


class TestGate:
    def test_passes_with_30_rows_and_enough_words(self):
        rows = [
            {
                "id": f"v{i}",
                "titulo": "t",
                "duracao_s": 500,
                "contagem_palavras": int(coleta.expected_word_count(500)),
                "fonte": "legenda",
            }
            for i in range(30)
        ]

        ok, problems = coleta.check_gate(rows)

        assert ok
        assert problems == []

    def test_passes_with_exactly_min_rows_and_enough_words(self):
        rows = [
            {
                "id": f"v{i}",
                "titulo": "t",
                "duracao_s": 500,
                "contagem_palavras": int(coleta.expected_word_count(500)),
                "fonte": "legenda",
            }
            for i in range(coleta.MIN_ROWS)
        ]

        ok, problems = coleta.check_gate(rows)

        assert ok
        assert problems == []

    def test_fails_one_row_below_min_rows_even_with_enough_words(self):
        rows = [
            {
                "id": f"v{i}",
                "titulo": "t",
                "duracao_s": 500,
                "contagem_palavras": int(coleta.expected_word_count(500)),
                "fonte": "legenda",
            }
            for i in range(coleta.MIN_ROWS - 1)
        ]

        ok, problems = coleta.check_gate(rows)

        assert not ok
        assert any(
            f"{coleta.MIN_ROWS - 1} linhas, esperado pelo menos {coleta.MIN_ROWS}" in p
            for p in problems
        )

    def test_fails_when_a_transcript_is_below_60_percent_of_expected_words(self):
        rows = [
            {
                "id": f"v{i}",
                "titulo": "t",
                "duracao_s": 500,
                "contagem_palavras": int(coleta.expected_word_count(500)),
                "fonte": "legenda",
            }
            for i in range(29)
        ]
        truncated_words = int(coleta.expected_word_count(500) * 0.5)
        rows.append(
            {
                "id": "truncated",
                "titulo": "t",
                "duracao_s": 500,
                "contagem_palavras": truncated_words,
                "fonte": "legenda",
            }
        )

        ok, problems = coleta.check_gate(rows)

        assert not ok
        assert any("truncated" in p for p in problems)


# --------------------------------------------------------------------------
# Pipeline: coleta interrompida
# --------------------------------------------------------------------------


class TestCollect:
    def test_writes_manifest_on_partial_success_when_a_video_fails(self, monkeypatch, tmp_path):
        # 5 videos selecionados; o 4o (indice 3) estoura um erro real de
        # rede/bloqueio de IP no meio da coleta - collect() precisa escrever
        # o manifesto com o que conseguiu (3 linhas), nao deixar o loop
        # inteiro quebrar sem persistir nada, e nao continuar tentando os
        # videos restantes.
        videos = [_video(f"v{i}", duration=500) for i in range(5)]
        monkeypatch.setattr(coleta, "list_channel_videos", lambda channel_url: videos)
        monkeypatch.setattr(coleta, "select_videos", lambda vids, target, now=None: vids[:target])

        def fake_collect_transcript(video_id):
            if video_id == "v3":
                raise IpBlocked(video_id)
            return [{"start": 0, "duration": 1, "text": "oi tudo bem"}], "youtube_transcript_api"

        monkeypatch.setattr(coleta, "collect_transcript", fake_collect_transcript)

        manifest_path = tmp_path / "manifesto.csv"
        raw_dir = tmp_path / "raw"

        rows = coleta.collect(
            target=5, raw_dir=raw_dir, manifest_path=manifest_path, sleep_seconds=0
        )

        assert [r["id"] for r in rows] == ["v0", "v1", "v2"]
        assert manifest_path.exists()
        assert len(coleta.read_manifesto(manifest_path)) == 3

    def test_writes_manifest_when_every_selected_video_succeeds(self, monkeypatch, tmp_path):
        videos = [_video(f"v{i}", duration=500) for i in range(3)]
        monkeypatch.setattr(coleta, "list_channel_videos", lambda channel_url: videos)
        monkeypatch.setattr(coleta, "select_videos", lambda vids, target, now=None: vids[:target])
        monkeypatch.setattr(
            coleta,
            "collect_transcript",
            lambda video_id: (
                [{"start": 0, "duration": 1, "text": "oi tudo bem"}],
                "youtube_transcript_api",
            ),
        )

        manifest_path = tmp_path / "manifesto.csv"
        raw_dir = tmp_path / "raw"

        rows = coleta.collect(
            target=3, raw_dir=raw_dir, manifest_path=manifest_path, sleep_seconds=0
        )

        assert [r["id"] for r in rows] == ["v0", "v1", "v2"]
        assert len(coleta.read_manifesto(manifest_path)) == 3

    def test_propagates_unexpected_exception_instead_of_writing_partial_manifest(
        self, monkeypatch, tmp_path
    ):
        # Um RuntimeError generico aqui nao e "sem legenda" nem "IP
        # bloqueado" - e um bug real (ex: KeyError/AttributeError de uma
        # regressao futura). collect() nao pode engolir isso: tem que
        # subir e o manifesto parcial nao pode ser escrito como se fosse
        # um stop esperado, porque isso faria check_gate() passar com
        # >= 21 linhas e esconder o defeito.
        videos = [_video(f"v{i}", duration=500) for i in range(5)]
        monkeypatch.setattr(coleta, "list_channel_videos", lambda channel_url: videos)
        monkeypatch.setattr(coleta, "select_videos", lambda vids, target, now=None: vids[:target])

        def fake_collect_transcript(video_id):
            if video_id == "v3":
                raise RuntimeError("bug de verdade, nao um stop esperado")
            return [{"start": 0, "duration": 1, "text": "oi tudo bem"}], "youtube_transcript_api"

        monkeypatch.setattr(coleta, "collect_transcript", fake_collect_transcript)

        manifest_path = tmp_path / "manifesto.csv"
        raw_dir = tmp_path / "raw"

        with pytest.raises(RuntimeError, match="bug de verdade"):
            coleta.collect(target=5, raw_dir=raw_dir, manifest_path=manifest_path, sleep_seconds=0)

        assert not manifest_path.exists()

    def test_still_stops_gracefully_on_whisperx_unavailable(self, monkeypatch, tmp_path):
        # WhisperXUnavailable e a falha externa conhecida (dependencia
        # ausente/audio nao baixado, ver fetch_via_whisperx) - continua
        # sendo tratada como stop esperado, so o RuntimeError generico e
        # que passou a subir.
        videos = [_video(f"v{i}", duration=500) for i in range(5)]
        monkeypatch.setattr(coleta, "list_channel_videos", lambda channel_url: videos)
        monkeypatch.setattr(coleta, "select_videos", lambda vids, target, now=None: vids[:target])

        def fake_collect_transcript(video_id):
            if video_id == "v3":
                raise coleta.WhisperXUnavailable("whisperX nao instalado")
            return [{"start": 0, "duration": 1, "text": "oi tudo bem"}], "youtube_transcript_api"

        monkeypatch.setattr(coleta, "collect_transcript", fake_collect_transcript)

        manifest_path = tmp_path / "manifesto.csv"
        raw_dir = tmp_path / "raw"

        rows = coleta.collect(
            target=5, raw_dir=raw_dir, manifest_path=manifest_path, sleep_seconds=0
        )

        assert [r["id"] for r in rows] == ["v0", "v1", "v2"]
        assert manifest_path.exists()

    def test_still_stops_gracefully_on_subprocess_called_process_error(self, monkeypatch, tmp_path):
        videos = [_video(f"v{i}", duration=500) for i in range(5)]
        monkeypatch.setattr(coleta, "list_channel_videos", lambda channel_url: videos)
        monkeypatch.setattr(coleta, "select_videos", lambda vids, target, now=None: vids[:target])

        def fake_collect_transcript(video_id):
            if video_id == "v3":
                raise subprocess.CalledProcessError(1, ["yt-dlp"])
            return [{"start": 0, "duration": 1, "text": "oi tudo bem"}], "youtube_transcript_api"

        monkeypatch.setattr(coleta, "collect_transcript", fake_collect_transcript)

        manifest_path = tmp_path / "manifesto.csv"
        raw_dir = tmp_path / "raw"

        rows = coleta.collect(
            target=5, raw_dir=raw_dir, manifest_path=manifest_path, sleep_seconds=0
        )

        assert [r["id"] for r in rows] == ["v0", "v1", "v2"]
        assert manifest_path.exists()

    def test_propagates_unrelated_bug_exception_type_too(self, monkeypatch, tmp_path):
        # Mesma garantia, tipo diferente: TypeError tambem nao esta na
        # lista de "parar aqui e esperado" e tem que subir.
        videos = [_video(f"v{i}", duration=500) for i in range(2)]
        monkeypatch.setattr(coleta, "list_channel_videos", lambda channel_url: videos)
        monkeypatch.setattr(coleta, "select_videos", lambda vids, target, now=None: vids[:target])

        def fake_collect_transcript(video_id):
            raise TypeError("regressao de verdade")

        monkeypatch.setattr(coleta, "collect_transcript", fake_collect_transcript)

        manifest_path = tmp_path / "manifesto.csv"
        raw_dir = tmp_path / "raw"

        with pytest.raises(TypeError, match="regressao de verdade"):
            coleta.collect(target=2, raw_dir=raw_dir, manifest_path=manifest_path, sleep_seconds=0)
