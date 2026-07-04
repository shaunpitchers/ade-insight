from __future__ import annotations

import json

from ade_insight.analysis.temperature import analyse_temperature


def test_analyse_temperature_writes_summary_and_stats(tmp_path):
    temp_file = tmp_path / "temp.csv"
    temp_file.write_text(
        "\n".join(
            [
                "time,1,2,ROOM TEMP 1,ROOM HUMIDITY 1",
                "2026-01-01 00:00:00,1.0,2.0,25.0,50.0",
                "2026-01-01 00:01:00,3.0,4.0,26.0,51.0",
            ]
        ),
        encoding="utf-8",
    )

    result = analyse_temperature(
        temp_file=temp_file,
        out_dir=tmp_path / "out",
        tz="Europe/London",
        time_base="datetime",
        stamp="run",
    )

    assert result.summary_path.exists()
    assert result.stats_path.exists()
    payload = json.loads(result.summary_path.read_text(encoding="utf-8"))
    assert payload["analysis_type"] == "temperature"
    assert payload["columns"]["selected_probes"] == ["1", "2"]
    assert payload["columns"]["ambient_temp"] == "ROOM TEMP 1"
    assert payload["overall"]["mean"] == 2.5
