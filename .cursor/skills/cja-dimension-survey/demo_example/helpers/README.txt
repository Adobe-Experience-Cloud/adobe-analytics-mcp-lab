Outputs folder — suggested artifacts (all under ../outputs/)
============================================================

Filenames are suggestions; nothing here is committed.

  usage_dimensions.json       listComponentUsage (dimension) excerpt or top-N slice
  usage_metrics.json          listComponentUsage (metric) excerpt or top-M slice
  metric_zero_pass.json       All_Visits row + metrics qualification (raw or trimmed)
  upsert_project_args.json    Last upsertProject envelope (expansions + projectBody)

Use UTF-8 without BOM (e.g. Python Path.write_text(..., encoding="utf-8")).
