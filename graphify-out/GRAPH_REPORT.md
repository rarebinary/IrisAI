# Graph Report - /Users/yann/Downloads/projects/PylaAI-main 2  (2026-07-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2598 nodes · 5464 edges · 124 communities (116 shown, 8 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 510 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- _read_text
- app.js
- _make_id
- resolution.py
- reflect.py
- deduplicate_entities
- hooks.py
- prs.py
- Path
- WebDataService
- Play
- serve.py
- utils.py
- cache.py
- main.py
- Path
- resolve_project_path
- skeleton.py
- RuntimeError
- dispatch_command
- export.py
- _collect_js_symbol_resolution_facts
- symbol_resolution.py
- extract_files_direct
- llm.py
- security.py
- _rebuild_code
- build.py
- write_callflow_html
- analyze.py
- html.py
- debug_view.py
- load_toml_as_dict
- install.py
- ingest.py
- scip_ingest.py
- generate_section_flowchart
- extract
- callflow_html.py
- diagnostics.py
- extract.py
- install
- detect
- _key
- Counter
- detect.py
- ControlSender
- TrophyObserver
- pick_text
- mcp_ingest.py
- manifest_ingest.py
- paths.py
- _build_http_app
- cluster.py
- _call_llm
- Path
- global_add
- state_finder.py
- edge_data
- _os_path
- affected.py
- semantic_cleanup.py
- dm.py
- google_workspace.py
- transcribe.py
- DiscordBot
- WindowController
- benchmark.py
- _get_extractor
- xlsx_to_markdown
- file_slice.py
- __main__.py
- Client
- Path
- _js_extra_walk
- verilog.py
- _agents_install
- _get_backend_api_key
- extract_objc
- powershell.py
- resolver_registry.py
- Detect
- setup.py
- _install_kilo_plugin
- generate
- log_query
- first_present
- introspect_cargo
- extract_lazarus_package
- _platform_skill_destination
- core.py
- .__init__
- graphdb.py
- extract_fortran
- extract_go
- extract_json
- extract_markdown
- extract_rust
- generate_community_labels
- sanitize_metadata
- _query_terms
- watch
- normalize_sections
- humanize_label
- _ts_emit_decorator_edges
- _label_batch_with_retry
- _resolve_name
- extract_sln
- extract_terraform
- pascal_resolution.py
- introspect_postgres
- validate_extraction
- deduplicate_by_label
- _uninstall_claude_hook
- .swipe
- __init__.py
- dedupe_edges
- dedupe_nodes
- distinct_repo_tags
- base.py
- __init__.py
- validate_url

## God Nodes (most connected - your core abstractions)
1. `_read_text()` - 82 edges
2. `dispatch_command()` - 58 edges
3. `_make_id()` - 52 edges
4. `WebDataService` - 51 edges
5. `_rebuild_code()` - 46 edges
6. `Play` - 46 edges
7. `_file_stem()` - 44 edges
8. `load_toml_as_dict()` - 38 edges
9. `dispatch_install_cli()` - 34 edges
10. `_extract_generic()` - 32 edges

## Surprising Connections (you probably didn't know these)
- `WindowController` --uses--> `DebugViewPublisher`  [INFERRED]
  window_controller.py → debug_view.py
- `DiscordBot` --uses--> `WindowController`  [INFERRED]
  discord_bot.py → window_controller.py
- `_SuppressAssetsGetting` --uses--> `DiscordBot`  [INFERRED]
  webui/app.py → discord_bot.py
- `_SuppressQueuePolling` --uses--> `DiscordBot`  [INFERRED]
  webui/app.py → discord_bot.py
- `_SuppressRuntimeStatusPolling` --uses--> `DiscordBot`  [INFERRED]
  webui/app.py → discord_bot.py

## Import Cycles
- None detected.

## Communities (124 total, 8 thin omitted)

### Community 0 - "_read_text"
Cohesion: 0.02
Nodes (126): _import_c(), _import_csharp(), _import_java(), _import_js(), _import_kotlin(), _import_lua(), _import_php(), _import_python() (+118 more)

### Community 1 - "app.js"
Cohesion: 0.06
Nodes (107): AUTH_ERROR_COPY, authMetaLine(), autosaveSection(), bindBrawlerCardEvents(), bindHistoryChartRangeControls(), bindPlaystyleCardEvents(), bindPlaystyleEvents(), bindQueueEvents() (+99 more)

### Community 2 - "_make_id"
Cohesion: 0.04
Nodes (66): extract_apex(), Path, Apex extractor. Moved verbatim from graphify/extract.py., Extract classes, interfaces, enums, methods, and Salesforce constructs from, _file_stem(), _make_id(), Path, Stem used as the node-ID prefix for a file and its symbols.      The full path ( (+58 more)

### Community 3 - "resolution.py"
Cohesion: 0.06
Nodes (70): extract_astro(), extract_svelte(), extract_vue(), Extract imports from .svelte files: script-block via JS AST + template regex fal, Extract imports from .astro files: frontmatter (TS) + template regex fallback., Extract imports, symbols, and type refs from a ``.vue`` SFC.      Masks the non-, _collect_python_symbol_resolution_facts(), _contained_in_package() (+62 more)

### Community 4 - "reflect.py"
Cohesion: 0.07
Nodes (57): aggregate_lessons(), _build_id_label_maps(), build_learning_overlay(), _code_fingerprint(), _content_hash(), _decay(), _dedupe_by_question(), _doc_community() (+49 more)

### Community 5 - "deduplicate_entities"
Cohesion: 0.07
Nodes (44): _collision_rank(), _crossfile_fileanchored_blocked(), deduplicate_entities(), _defines_id(), _entropy(), _id_prefixes(), _is_code(), _is_variant_pair() (+36 more)

### Community 6 - "hooks.py"
Cohesion: 0.07
Nodes (49): _detached_launch(), _git_root(), _has_merge_attr(), _hooks_dir(), install(), _install_hook(), _merge_attr_line(), _merge_driver_status() (+41 more)

### Community 7 - "prs.py"
Cohesion: 0.11
Nodes (44): attach_graph_impact(), bold(), build_community_labels(), _c(), _ci_icon(), _classify(), cmd_prs(), compute_pr_impact() (+36 more)

### Community 8 - "Path"
Cohesion: 0.09
Nodes (47): _agents_platform_uninstall(), _agents_uninstall(), _amp_uninstall(), _antigravity_uninstall(), claude_uninstall(), codebuddy_uninstall(), _cursor_uninstall(), _devin_rules_uninstall() (+39 more)

### Community 9 - "WebDataService"
Cohesion: 0.15
Nodes (7): clean_queue(), get_discord_link(), load_brawler_data(), get_brawler_stats(), get_player_info(), Any, WebDataService

### Community 10 - "Play"
Cohesion: 0.08
Nodes (3): add_advanced_visuals(), Play, count_hsv_pixels()

### Community 11 - "serve.py"
Cohesion: 0.10
Nodes (41): Strip control characters and cap length.      Safe for embedding in JSON data (i, sanitize_label(), _bfs(), _communities_from_graph(), _community_header(), _compute_idf(), _dfs(), _filter_graph_by_context() (+33 more)

### Community 12 - "utils.py"
Cohesion: 0.09
Nodes (32): api_update_brawler_data(), calculate_sha256(), check_version(), clamp(), clear_brawler_data(), count_mask_pixels(), current_wall_model_is_latest(), get_brawler_info() (+24 more)

### Community 13 - "cache.py"
Cohesion: 0.10
Nodes (40): _absolutize_source_files_in(), _body_content(), cache_dir(), cached_files(), cached_word_count(), check_semantic_cache(), _cleanup_stale_ast_entries(), clear_cache() (+32 more)

### Community 14 - "main.py"
Cohesion: 0.10
Nodes (15): apply_play_order(), pyla_main(), get_brawler_stats(), get_player_info(), load_image(), StageManager, get_state(), TimeManagement (+7 more)

### Community 15 - "Path"
Cohesion: 0.07
Nodes (39): extract_c(), extract_cpp(), extract_groovy(), extract_java(), extract_js(), _extract_js_rationale(), extract_kotlin(), extract_lua() (+31 more)

### Community 16 - "resolve_project_path"
Cohesion: 0.10
Nodes (15): Flask, LogRecord, get_brawler_icon_path(), Path, resolve_project_path(), _configure_request_logging(), create_app(), _start_discord_bot_thread() (+7 more)

### Community 17 - "skeleton.py"
Cohesion: 0.05
Nodes (38): attack(), find_closest_enemy(), find_closest_teammate(), get_actual_player_box(), get_brawler_range(), get_distance(), get_entity_pos(), get_random_movement() (+30 more)

### Community 18 - "RuntimeError"
Cohesion: 0.09
Nodes (35): _anthropic_content(), _backend_pkg_hint(), _bedrock_content(), _call_azure(), _call_bedrock(), _call_claude(), _call_claude_cli(), _call_openai_compat() (+27 more)

### Community 19 - "dispatch_command"
Cohesion: 0.10
Nodes (32): _clone_repo(), _default_graph_path(), dispatch_command(), _enforce_graph_size_cap_or_exit(), _hook_strict_enabled(), _mark_session_denied(), _prune_graph_json_sources(), Path (+24 more)

### Community 20 - "export.py"
Cohesion: 0.09
Nodes (35): attach_hyperedges(), backup_if_protected(), _cap_filename(), _cypher_escape(), _cypher_label(), _dedup_node_filenames(), existing_graph_node_count(), _git_head() (+27 more)

### Community 21 - "_collect_js_symbol_resolution_facts"
Cohesion: 0.08
Nodes (34): _augment_js_reexport_edges(), Compatibility wrapper for the JS/TS symbol-resolution post-pass., _NamespaceExportFact, models — moved verbatim from graphify/extract.py., _StarExportFact, _SymbolAliasFact, _SymbolDeclarationFact, _SymbolExportFact (+26 more)

### Community 22 - "symbol_resolution.py"
Cohesion: 0.11
Nodes (34): _bash_make_id(), build_label_index(), build_python_symbol_index(), existing_edge_pairs(), _file_node_id_for_path(), find_unique_python_symbol(), ImportedSymbol, iter_raw_calls() (+26 more)

### Community 23 - "extract_files_direct"
Cohesion: 0.11
Nodes (34): FileSlice, Read just this slice's characters from its parent file., A contiguous ``[start, end)`` character range of a splittable text file.      ``, The on-disk path a unit belongs to (the parent file for a slice)., read_slice_text(), unit_path(), _bind_node_evidence(), _build_image_refs() (+26 more)

### Community 24 - "llm.py"
Cohesion: 0.06
Nodes (33): _backend_supports_vision(), _custom_providers_path(), estimate_cost(), _get_tokenizer(), _label_identifiers(), _load_custom_providers(), _looks_like_context_exceeded(), _mark_partial() (+25 more)

### Community 25 - "security.py"
Cohesion: 0.11
Nodes (22): _build_opener(), check_graph_file_size_cap(), _max_graph_file_bytes(), Path, Resolve *host* once and return (family, validated_ip) for the first     address, HTTPConnection that resolves + validates DNS once, then connects to the     exac, HTTPSConnection variant of _SSRFGuardedHTTPConnection.      Connects to the vali, urllib handler that routes http:// through _SSRFGuardedHTTPConnection. (+14 more)

### Community 26 - "_rebuild_code"
Cohesion: 0.10
Nodes (31): _apply_resource_limits(), _canonical_graph_for_compare(), _canonical_topology_for_compare(), _changed_path_candidates(), _check_shrink(), _drain_pending(), _git_head(), _json_text() (+23 more)

### Community 27 - "build.py"
Cohesion: 0.14
Nodes (29): build(), build_from_json(), build_merge(), _doc_twin_remap(), edge_datas(), graph_has_legacy_ids(), _infer_merge_root(), _norm_source_file() (+21 more)

### Community 28 - "write_callflow_html"
Cohesion: 0.09
Nodes (30): CallflowOptions, classify_edges(), first_list(), html_comment_text(), infer_project_name(), load_graph(), load_labels(), load_report() (+22 more)

### Community 29 - "analyze.py"
Cohesion: 0.13
Nodes (29): _cross_community_surprises(), _cross_file_surprises(), _cross_language(), _file_category(), god_nodes(), graph_diff(), _is_concept_node(), _is_file_node() (+21 more)

### Community 30 - "html.py"
Cohesion: 0.11
Nodes (27): _html_script(), _html_styles(), _hyperedge_script(), Graph, html — moved verbatim from graphify/export.py., Return the effective viz node limit, honoring GRAPHIFY_VIZ_NODE_LIMIT env var., Generate an interactive vis.js HTML visualization of the graph.      Features: n, to_html() (+19 more)

### Community 31 - "debug_view.py"
Cohesion: 0.15
Nodes (13): DebugClipRecorder, DebugViewPublisher, draw_boxes(), draw_debug_data(), draw_joystick_path_probe(), draw_lines(), draw_player_hit_circle(), draw_poison_gas_lines() (+5 more)

### Community 32 - "load_toml_as_dict"
Cohesion: 0.14
Nodes (12): LobbyAutomation, config_bool(), DefaultEasyOCR, EasyOCRInitializationError, extract_text_and_positions(), invalidate_toml_cache(), load_all_brawlers_names(), load_toml_as_dict() (+4 more)

### Community 33 - "install.py"
Cohesion: 0.13
Nodes (25): _always_on(), claude_install(), _claude_pretooluse_hooks(), codebuddy_install(), _gemini_hook(), _install_claude_hook(), _install_codebuddy_hook(), _install_codex_hook() (+17 more)

### Community 34 - "ingest.py"
Cohesion: 0.16
Nodes (22): _detect_url_type(), _download_binary(), _fetch_arxiv(), _fetch_html(), _fetch_tweet(), _fetch_webpage(), _html_to_markdown(), ingest() (+14 more)

### Community 35 - "scip_ingest.py"
Cohesion: 0.14
Nodes (24): _build_scip_metadata(), _coerce_str(), _emit_relationships(), _emit_symbol_node(), _first_occurrence_line(), ingest_scip_json(), _is_true(), _make_scip_node_id() (+16 more)

### Community 36 - "generate_section_flowchart"
Cohesion: 0.11
Nodes (24): generate_overview_graph(), generate_section_flowchart(), group_nodes_by_file(), mermaid_class_defs(), mermaid_init(), mermaid_section_id(), node_kind(), node_label() (+16 more)

### Community 37 - "extract"
Cohesion: 0.09
Nodes (24): _canonicalize_csharp_namespace_nodes(), _check_tree_sitter_version(), extract(), _extract_parallel(), _extract_single_file(), _file_node_id(), _is_top_level_function_definition(), _lang_family() (+16 more)

### Community 38 - "callflow_html.py"
Cohesion: 0.11
Nodes (22): build_community_index(), build_section_node_map(), _community_text(), derive_sections_from_communities(), detect_lang(), generate_header(), generate_nav(), _keyword_score() (+14 more)

### Community 39 - "diagnostics.py"
Cohesion: 0.19
Nodes (22): _canonical_edge(), _count_extra(), diagnose_extraction(), diagnose_file(), _edge_list(), _exact_signature(), format_diagnostic_json(), format_diagnostic_report() (+14 more)

### Community 40 - "extract.py"
Cohesion: 0.17
Nodes (22): extract_csharp(), extract_xaml(), _get_c_func_name(), Deterministic structural extraction from source code using tree-sitter. Outputs, Extract C# type declarations, methods, namespaces, and usings from a .cs file., Extract WPF/XAML structure, bindings, x:Class, and event handler references., Recursively unwrap declarator to find the innermost identifier (C)., _xaml_binding_refs() (+14 more)

### Community 41 - "install"
Cohesion: 0.13
Nodes (23): _canonical_platform(), _copy_skill_file(), _cursor_install(), _devin_rules_install(), gemini_install(), install(), _kiro_install(), _packaged_skill_refs_dir() (+15 more)

### Community 42 - "detect"
Cohesion: 0.12
Nodes (22): detect(), _find_vcs_root(), _git_info_exclude(), _is_ignored(), _is_noise_dir(), _load_dir_own_ignore(), _load_graphifyignore(), _load_graphifyinclude() (+14 more)

### Community 43 - "_key"
Cohesion: 0.12
Nodes (20): Resolve cross-file Swift member calls (``recv.method()``) to the real     defini, Resolve cross-file Python qualified class-method calls (``ClassName.method()``), Resolve cross-file TS/JS member calls via constructor-injection type tables (#13, Resolve C# member calls (``recv.Method()``) to the receiver's declared type, Resolve Java member calls against the receiver's declared type.      Explicit ty, Resolve cross-file Objective-C message sends (``[recv sel]``) to the real     de, _resolve_cpp_member_calls(), _resolve_csharp_member_calls() (+12 more)

### Community 44 - "Counter"
Cohesion: 0.12
Nodes (21): derive_flow_chain(), edge_score(), generate_overview_cards(), node_degree_scores(), node_importance(), preferred_edges(), Counter, Aggregate inter-section edge counts and relation names. (+13 more)

### Community 45 - "detect.py"
Cohesion: 0.10
Nodes (19): _auto_follow_symlinks(), _could_contain_included_path(), _env_command_args(), FileType, _generic_keyword_hit(), _is_included(), _match_anchored_ignore_pattern(), Enum (+11 more)

### Community 46 - "ControlSender"
Cohesion: 0.10
Nodes (9): ControlSender, If the screen is off, it is turned on only on ACTION_DOWN          Args:, Expand notification panel, Expand settings panel, Set clipboard          Args:             text: the string you want to set, Set screen power mode          Args:             mode: POWER_MODE_OFF | POWER_MO, Send keycode to device          Args:             keycode: const.KEYCODE_*, Send text to device          Args:             text: text to send (+1 more)

### Community 47 - "TrophyObserver"
Cohesion: 0.17
Nodes (7): GameMode, MatchResult, ParsedGameResult, Enum, Parses raw game result string into a structured data class., TrophyObserver, hash_playstyle()

### Community 48 - "pick_text"
Cohesion: 0.13
Nodes (20): _describe_node(), format_node_refs(), generate_call_table_rows(), generate_section_cards(), generate_section_intro(), is_zh(), pick_text(), Render node references as readable labels instead of internal IDs. (+12 more)

### Community 49 - "mcp_ingest.py"
Cohesion: 0.16
Nodes (19): _extract_spock_fallback(), Regex-based fallback for Spock spec files where tree-sitter-groovy cannot parse, _add_edge(), _add_node(), _detect_package_from_args(), _emit_server(), extract_mcp_config(), is_mcp_config_path() (+11 more)

### Community 50 - "manifest_ingest.py"
Cohesion: 0.13
Nodes (17): _coerce_deps(), extract_package_manifest(), is_package_manifest_path(), _parse_apm(), _parse_apm_fallback(), _parse_pyproject(), _pep508_name(), _pkg_id() (+9 more)

### Community 51 - "paths.py"
Cohesion: 0.14
Nodes (18): _atomic_replace(), default_graph_json(), disambiguate_ambiguous_candidates(), _is_test_path(), out_path(), _path_proximity_winner(), Path, Single source of truth for the graphify output-directory name.  The output direc (+10 more)

### Community 52 - "_build_http_app"
Cohesion: 0.11
Nodes (15): _ApiKeyMiddleware, _build_http_app(), _build_server(), _filter_blank_stdin(), _main(), _MCPASGIApp, Build the configured low-level MCP Server (shared by every transport).      All, Start the MCP server over stdio (the default, per-developer transport). (+7 more)

### Community 53 - "cluster.py"
Cohesion: 0.18
Nodes (17): cluster(), cohesion_score(), label_communities_by_hub(), _partition(), Graph, Community detection on NetworkX graphs. Uses Leiden (graspologic) if available,, Context manager to suppress stdout/stderr during library calls.      graspologic, Run Leiden community detection. Returns {community_id: [node_ids]}.      Communi (+9 more)

### Community 54 - "_call_llm"
Cohesion: 0.12
Nodes (18): _azure_client(), _bedrock_inference_config(), _call_llm(), _default_model_for_backend(), _model_requires_default_temperature(), _no_window_kwargs(), Return configured model override or backend default model., Construct an AzureOpenAI client with env-driven api_version and timeout. (+10 more)

### Community 55 - "Path"
Cohesion: 0.24
Nodes (11): check_update(), _is_relative_to(), Path, Check for pending semantic update flag and notify the user if set.      Cron-saf, Resolve source_file values across current and legacy graph roots., Merge fresh extraction with preserved graph entries and evict stale sources., Persist corpus-shaping options under ``out_dir``.      Best effort and non clobb, _reconcile_existing_graph() (+3 more)

### Community 56 - "global_add"
Cohesion: 0.22
Nodes (16): prune_repo_from_graph(), Remove all nodes tagged with repo_tag from G in-place. Returns count removed., _file_hash(), global_add(), global_list(), global_path(), global_remove(), _load_global_graph() (+8 more)

### Community 57 - "state_finder.py"
Cohesion: 0.31
Nodes (16): find_game_result(), get_in_game_state(), is_in_brawl_pass(), is_in_brawler_selection(), is_in_end_of_a_match(), is_in_lobby(), is_in_match_making(), is_in_nano_noodles() (+8 more)

### Community 58 - "edge_data"
Cohesion: 0.23
Nodes (15): edge_data(), Return one edge attribute dict for (u, v), tolerating MultiGraph.      For Multi, _community_article(), _cross_community_links(), _god_node_article(), _index_md(), _md_link(), Graph (+7 more)

### Community 59 - "_os_path"
Cohesion: 0.15
Nodes (16): detect_incremental(), load_manifest(), _md5_file(), _os_path(), r"""Return an OS path string safe for open()/stat() on Windows long paths., MD5 of file contents streamed in 64KB chunks — for change detection only., Stat + MD5 a single file; returns None on OSError (e.g. deleted mid-run)., Return ``key`` as a forward-slash relative path from ``root``.      Keys outside (+8 more)

### Community 60 - "affected.py"
Cohesion: 0.29
Nodes (14): affected_nodes(), AffectedHit, _bare_name(), format_affected(), _format_location(), load_graph(), _node_label(), _normalize_label() (+6 more)

### Community 61 - "semantic_cleanup.py"
Cohesion: 0.19
Nodes (14): _normalize_hyperedge_members(), Canonicalize a hyperedge's member list onto the `nodes` key, in place.      If `, _append_rationale_attr(), _is_sentence_like_rationale_label(), load_validated_semantic_fragment(), Path, Load and validate a semantic chunk, rejecting oversize files before parsing., Clean up a semantic extraction fragment in-place.      Operations:     1. Remove (+6 more)

### Community 62 - "dm.py"
Cohesion: 0.19
Nodes (14): _dmm_type_path(), extract_dm(), extract_dmf(), extract_dmi(), extract_dmm(), Path, Dm extractor. Moved verbatim from graphify/extract.py., Extract types, procs, includes, and calls from a .dm/.dme file. (+6 more)

### Community 63 - "google_workspace.py"
Cohesion: 0.24
Nodes (14): convert_google_workspace_file(), _extract_file_id_from_url(), _extract_resource_key(), Any, Path, Optional Google Workspace shortcut export support.  Google Drive for desktop sto, Export a Google Workspace shortcut to a Markdown sidecar.      Returns the conve, Extract a Drive file ID from common Google Docs/Drive URL shapes. (+6 more)

### Community 64 - "transcribe.py"
Cohesion: 0.21
Nodes (14): build_whisper_prompt(), download_audio(), _get_whisper(), _get_yt_dlp(), is_url(), _model_name(), Path, Transcribe a video/audio file or URL to a .txt transcript.      If video_path is (+6 more)

### Community 65 - "DiscordBot"
Cohesion: 0.21
Nodes (3): DiscordBot, register_early_access_commands(), Interaction

### Community 67 - "benchmark.py"
Cohesion: 0.20
Nodes (13): _estimate_tokens(), _hr(), print_benchmark(), Graph, _query_subgraph_tokens(), Token-reduction benchmark - measures how much context graphify saves vs naive fu, Print a human-readable benchmark report., Return unicode_char if stdout can encode it, else ascii_fallback.      Windows c (+5 more)

### Community 68 - "_get_extractor"
Cohesion: 0.15
Nodes (13): _get_extractor(), _is_cpp_header(), _is_objc_header(), _is_objc_source(), Any, Whether a `.h` file is Objective-C rather than C/C++ (#1475).      `.h` is share, Whether a `.m` file is Objective-C rather than MATLAB/Octave (#1702).      `.m`, Whether a `.h` file is C++ rather than plain C (#1547).      Mirrors `_is_objc_h (+5 more)

### Community 69 - "xlsx_to_markdown"
Cohesion: 0.19
Nodes (13): convert_office_file(), count_words(), docx_to_markdown(), extract_pdf_text(), _file_within_size_cap(), Extract plain text from a PDF file using pypdf., Convert a .docx file to markdown text using python-docx., True if *path* exists and its on-disk size is within *cap*. (+5 more)

### Community 70 - "file_slice.py"
Cohesion: 0.21
Nodes (12): _best_cut(), bisect_slice(), expand_oversized_files(), is_splittable_text(), Path, Intra-file slicing for oversized text documents (#1369).  The extraction packer, Replace each oversized splittable-text file with a list of ``FileSlice``s., Split a slice into two halves at a newline near its midpoint, or None.      Used (+4 more)

### Community 71 - "__main__.py"
Cohesion: 0.21
Nodes (12): _check_skill_version(), __getattr__(), main(), Path, graphify CLI - `graphify install` sets up the Claude Code skill., Warn if the installed skill is from an older graphify version., Parse a version string into a comparable integer tuple (``0.9.2`` -> ``(0, 9, 2), Handle a downstream reader that closed the pipe early. Redirect stdout to     de (+4 more)

### Community 72 - "Client"
Cohesion: 0.23
Nodes (7): Client, Connect to android server, there will be two sockets, video and control socket., Deploy server to android device, Start listening video stream          Args:             threaded: Run stream loo, Stop listening (both threaded and blocked), Core loop for video parsing with frame skipping, Send event to listeners          Args:             cls: Listener type

### Community 73 - "Path"
Cohesion: 0.24
Nodes (12): classify_file(), _is_graphable_source(), _is_sensitive(), _looks_like_paper(), Path, True for genuine programming-language source — the only category exempt     from, Return True if this file likely contains secrets and should be skipped., Heuristic: does this text file read like an academic paper? (+4 more)

### Community 74 - "_js_extra_walk"
Cohesion: 0.17
Nodes (12): _find_require_call(), _js_collect_pattern_idents(), _js_extra_walk(), _js_local_bound_names(), _js_member_assignment_target(), Collect binding identifier names from a JS/TS pattern (a parameter, or a     dec, Names bound locally inside a JS/TS function: parameters plus `const`/`let`/, Return the call_expression node if `value_node` is a `require(...)` call     or (+4 more)

### Community 75 - "verilog.py"
Cohesion: 0.24
Nodes (10): _augment_systemverilog_semantics(), extract_verilog(), Path, Verilog extractor. Moved verbatim from graphify/extract.py., First `simple_identifier` under node in pre-order, or None.      tree-sitter-ver, Extract modules, functions, tasks, package imports, instantiations, and     Syst, _sv_collect_type_refs(), _sv_first_identifier() (+2 more)

### Community 76 - "_agents_install"
Cohesion: 0.17
Nodes (12): _agents_install(), _agents_platform_install(), _amp_install(), _amp_legacy_cleanup(), _install_opencode_plugin(), _kilo_install(), Write graphify.js plugin and register it in opencode.json., Write the graphify section to the local AGENTS.md for always-on platforms. (+4 more)

### Community 77 - "_get_backend_api_key"
Cohesion: 0.17
Nodes (12): _backend_env_keys(), detect_backend(), _format_backend_env_keys(), _get_backend_api_key(), _ollama_host_is_link_local_or_metadata(), Return accepted API-key environment variables for a backend., Return the first configured API key for backend, or an empty string., Return user-facing accepted API-key variable names. (+4 more)

### Community 78 - "extract_objc"
Cohesion: 0.20
Nodes (10): _cpp_declarator_name(), _cpp_local_var_types(), Return the bare variable name from a C++ declaration declarator, unwrapping, Collect ``var -> ClassName`` from local variable declarations in a C++     funct, extract_objc(), _objc_local_var_types(), Path, objc — moved verbatim from graphify/extract.py. (+2 more)

### Community 79 - "powershell.py"
Cohesion: 0.20
Nodes (10): extract_powershell(), extract_powershell_manifest(), _psd1_collect_string_literals(), _psd1_module_name(), Path, Powershell extractor. Moved verbatim from graphify/extract.py., Extract functions, classes, methods, and using statements from a .ps1 file., Recursively collect all string_literal text values under *node*. (+2 more)

### Community 80 - "resolver_registry.py"
Cohesion: 0.24
Nodes (10): LanguageResolver, Path, Registry for cross-file, language-specific resolution passes.  Some call/referen, One cross-file, language-specific resolution pass.      ``resolve`` has the sign, Append a resolver to the global registry and return it (for inline use)., Return a copy of the registered resolvers, in registration order., Run every resolver whose suffix appears in ``paths``.      Behaviorally identica, register() (+2 more)

### Community 81 - "Detect"
Cohesion: 0.29
Nodes (5): Detect, _normalize_yolo_output(), _numpy_nms(), _postprocess_raw(), Accepts either:         outputs         outputs[0]      Supports common YOLO ONN

### Community 82 - "setup.py"
Cohesion: 0.22
Nodes (5): check_base_requirements(), check_pytorch_status(), get_requirement_name(), is_windows(), Returns 'cuda', 'mps', 'cpu', or 'missing'.

### Community 83 - "_install_kilo_plugin"
Cohesion: 0.24
Nodes (10): _install_kilo_plugin(), _kilo_config_path(), _kilo_config_write_path(), _load_json_like(), Remove JSONC-style comments while leaving string content intact., Write automated Kilo edits to kilo.json so existing JSONC stays untouched., Write graphify.js plugin and register it without rewriting user JSONC., Remove graphify.js plugin and deregister it without rewriting user JSONC. (+2 more)

### Community 84 - "generate"
Cohesion: 0.31
Nodes (8): find_import_cycles(), Detect circular import dependencies at the file level.      Collapses symbol-lev, generate(), _learning_section(), Graph, Append the ``## Work-memory lessons`` section, or nothing when empty., Mirrors export.safe_name so community hub filenames and report wikilinks always, _safe_community_name()

### Community 85 - "log_query"
Cohesion: 0.31
Nodes (8): _log_path(), log_query(), _log_responses(), nodes_from_result(), Any, Path, Query logging for graphify — append-only JSONL, fail-silent., Append one JSONL record to the query log. Never raises.

### Community 86 - "first_present"
Cohesion: 0.29
Nodes (8): endpoint_id(), first_present(), normalize_edge(), normalize_node(), Return the first non-empty value for any candidate key., Normalize edge endpoints that may be strings or node-like objects., Normalize a graphify node across common graph.json schema variants., Normalize graphify edges while preserving original fields.

### Community 87 - "introspect_cargo"
Cohesion: 0.46
Nodes (7): introspect_cargo(), _load_toml(), _member_manifest_paths(), Any, Path, Cargo manifest introspection for workspace-internal crate dependencies., Return crate nodes and internal dependency edges from Cargo manifests.

### Community 88 - "extract_lazarus_package"
Cohesion: 0.25
Nodes (8): extract_csproj(), extract_lazarus_package(), extract_slnx(), _project_xml_is_safe(), Reject XML that declares DTDs or entities.      Stdlib ``xml.etree.ElementTree``, Extract package metadata from Lazarus .lpk package files (XML format).      .lpk, Extract projects and inter-project dependencies from a .slnx file.      .slnx is, Extract packages, project refs, and target framework from a .csproj/.fsproj/.vbp

### Community 89 - "_platform_skill_destination"
Cohesion: 0.25
Nodes (8): _antigravity_finalize(), _antigravity_install(), _platform_skill_destination(), After a successful install, update .graphify_version in all other known skill di, Return the skill destination for a platform and scope., Write Antigravity's always-on layer next to an installed skill.      Injects the, Install graphify for Google Antigravity (global skill + .agents/rules + .agents/, _refresh_all_version_stamps()

### Community 90 - "core.py"
Cohesion: 0.32
Nodes (4): This module includes all consts used in this project, inject(), Inject control code, with this inject, we will be able to do unit test      Args, Python Scrcpy Client's core module

### Community 91 - ".__init__"
Cohesion: 0.25
Nodes (5): AdbDevice, any, Add a video listener          Args:             cls: Listener category, support:, Remove a video listener          Args:             cls: Listener category, suppo, Create a scrcpy client, this client won't be started until you call the start fu

### Community 92 - "graphdb.py"
Cohesion: 0.33
Nodes (6): push_to_falkordb(), push_to_neo4j(), Graph, graphdb — moved verbatim from graphify/export.py., Push graph directly to a running Neo4j instance via the Python driver.      Requ, Push graph directly to a running FalkorDB instance via the Python SDK.      Requ

### Community 93 - "extract_fortran"
Cohesion: 0.38
Nodes (6): _cpp_preprocess(), extract_fortran(), Path, Fortran extractor. Moved verbatim from graphify/extract.py., Run cpp -w -P on a capital-F Fortran file and return preprocessed bytes.      Fa, Extract programs, modules, subroutines, functions, use statements, and calls fro

### Community 94 - "extract_go"
Cohesion: 0.29
Nodes (6): extract_go(), _go_collect_type_refs(), Path, Go extractor. Moved verbatim from graphify/extract.py., Walk a Go type expression; append (name, role) tuples., Extract functions, methods, type declarations, and imports from a .go file.

### Community 95 - "extract_json"
Cohesion: 0.38
Nodes (6): extract_json(), _is_config_json(), Path, Json_config extractor. Moved verbatim from graphify/extract.py., True if a .json file is a recognized config/manifest worth AST-extracting., Extract structure and dependency edges from a *config/manifest* .json file.

### Community 96 - "extract_markdown"
Cohesion: 0.33
Nodes (6): extract_markdown(), Path, Markdown extractor. Moved verbatim from graphify/extract.py., Resolve a markdown link target to the absolute path of a sibling document., Extract structural nodes and edges from a Markdown file.      Produces nodes for, _resolve_markdown_link()

### Community 97 - "extract_rust"
Cohesion: 0.29
Nodes (6): extract_rust(), Path, Rust extractor. Moved verbatim from graphify/extract.py., Walk a Rust type expression; append (name, role) tuples., Extract functions, structs, enums, traits, impl methods, and use declarations fr, _rust_collect_type_refs()

### Community 98 - "generate_community_labels"
Cohesion: 0.33
Nodes (7): _community_label_lines(), generate_community_labels(), label_communities(), _placeholder_community_labels(), One prompt line per community (largest first), sampling up to ``top_k``     repr, Return a complete ``{cid: name}`` map using ``backend`` for naming.      Communi, CLI entry point: resolve a backend, name communities, and degrade to     ``Commu

### Community 99 - "sanitize_metadata"
Cohesion: 0.33
Nodes (7): Any, Return a control-character-free, HTML-escaped, bounded string., Sanitize a metadata value while preserving simple JSON-compatible types., Sanitize metadata keys and values before graph export.      Metadata is less con, sanitize_metadata(), _sanitize_metadata_string(), _sanitize_metadata_value()

### Community 100 - "_query_terms"
Cohesion: 0.29
Nodes (7): _has_chinese(), _is_searchable(), _query_terms(), True if term is Chinese, non-English, or an English word longer than 2 chars., Split a query into searchable terms, segmenting Chinese text, then drop     ques, Segment Chinese text and keep the original term for exact matching., _segment_chinese()

### Community 101 - "watch"
Cohesion: 0.29
Nodes (7): _has_non_code(), _notify_only(), Return whether rebuilds should honor VCS ignore files (default True)., Write a flag file and print a notification (fallback for non-code-only corpora)., Watch watch_path for new or modified files and auto-update the graph.      For c, _read_build_gitignore(), watch()

### Community 102 - "normalize_sections"
Cohesion: 0.33
Nodes (6): html_anchor_id(), normalize_communities(), normalize_sections(), Generate a stable, unique HTML anchor ID., Normalize section community lists from JSON or simple strings., Ensure sections have safe unique IDs and an overview section first.

### Community 103 - "humanize_label"
Cohesion: 0.33
Nodes (6): humanize_label(), node_display_name(), Readable node label for tables and summaries., Truncate without splitting Mermaid syntax., Convert graph labels into short labels people can scan in a diagram., truncate_text()

### Community 104 - "_ts_emit_decorator_edges"
Cohesion: 0.33
Nodes (6): Name of a `method_definition`, matching the id the function-types branch     bui, Collect `decorator` nodes under `node` (e.g. parameter decorators inside a     m, Emit `references` edges (context="decorator") from a class and its members     t, _ts_descendant_decorators(), _ts_emit_decorator_edges(), _ts_method_name()

### Community 105 - "_label_batch_with_retry"
Cohesion: 0.33
Nodes (6): _label_batch_with_retry(), _parse_label_response(), Honour GRAPHIFY_MAX_OUTPUT_TOKENS env var override, else use backend default., Parse the backend's JSON ``{cid: name}`` reply. Raises on non-JSON or a     non-, Label a batch of communities, splitting in half and retrying on parse failure., _resolve_max_tokens()

### Community 106 - "_resolve_name"
Cohesion: 0.40
Nodes (5): Get the name from a node using config.name_field, falling back to child types., _resolve_name(), _find_body(), Find the body node using config.body_field, falling back to child types., LanguageConfig

### Community 107 - "extract_sln"
Cohesion: 0.40
Nodes (4): extract_sln(), Path, Sln extractor. Moved verbatim from graphify/extract.py., Extract projects and inter-project dependencies from a .sln file.

### Community 108 - "extract_terraform"
Cohesion: 0.40
Nodes (4): extract_terraform(), Path, Terraform extractor. Moved verbatim from graphify/extract.py., Extract Terraform/HCL blocks and the references between them via tree-sitter.

### Community 109 - "pascal_resolution.py"
Cohesion: 0.50
Nodes (4): _pascal_raw_calls(), Cross-file resolution for Pascal/Delphi calls to inherited methods.  The per-fil, Resolve Pascal/Delphi calls to a method inherited across file boundaries.      P, resolve_pascal_inherited_calls()

### Community 110 - "introspect_postgres"
Cohesion: 0.50
Nodes (4): introspect_postgres(), _quote_ident(), Connect to PostgreSQL, reconstruct DDL, and extract via extract_sql()., Double-quote a PostgreSQL identifier, escaping embedded double-quotes.

### Community 111 - "validate_extraction"
Cohesion: 0.50
Nodes (4): assert_valid(), Validate an extraction JSON dict against the graphify schema.     Returns a list, Raise ValueError with all errors if extraction is invalid., validate_extraction()

### Community 112 - "deduplicate_by_label"
Cohesion: 0.50
Nodes (4): deduplicate_by_label(), _norm_label(), Canonical dedup key — Unicode-aware, preserves CJK/word characters., Merge nodes that share a normalised label, rewriting edge references.      Prefe

### Community 113 - "_uninstall_claude_hook"
Cohesion: 0.50
Nodes (4): Remove the graphify PreToolUse hook from .claude/settings.json and its     local, Drop graphify PreToolUse hooks from a single Claude settings file, if present., _strip_graphify_hook(), _uninstall_claude_hook()

### Community 123 - "validate_url"
Cohesion: 0.22
Nodes (8): _ip_is_blocked(), _NoFileRedirectHandler, Raise ValueError if *url* is not http or https, or targets a private/internal IP, Redirect handler that re-validates every redirect target.      Prevents open-red, Return True if *ip* falls in a private/reserved/internal range.      Shared by v, validate_url(), IPv4Address, IPv6Address

## Knowledge Gaps
- **5 isolated node(s):** `NAV_ITEMS`, `GAMEMODE_LABELS`, `AUTH_ERROR_COPY`, `state`, `SETTINGS_META`
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `dispatch_command()` connect `dispatch_command` to `prs.py`, `WebDataService`, `serve.py`, `cache.py`, `export.py`, `llm.py`, `_rebuild_code`, `build.py`, `analyze.py`, `html.py`, `diagnostics.py`, `paths.py`, `cluster.py`, `Path`, `global_add`, `edge_data`, `affected.py`, `semantic_cleanup.py`, `benchmark.py`, `__main__.py`, `_get_backend_api_key`, `generate`, `introspect_cargo`, `generate_community_labels`, `introspect_postgres`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Why does `_rebuild_code()` connect `_rebuild_code` to `_get_extractor`, `extract`, `watch`, `_os_path`, `detect`, `dispatch_command`, `export.py`, `cluster.py`, `generate`, `Path`, `security.py`, `build.py`, `write_callflow_html`, `analyze.py`, `html.py`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `_file_stem()` connect `_make_id` to `_read_text`, `resolution.py`, `Path`, `_collect_js_symbol_resolution_facts`, `build.py`, `extract`, `extract.py`, `mcp_ingest.py`, `dm.py`, `_js_extra_walk`, `verilog.py`, `extract_objc`, `powershell.py`, `extract_lazarus_package`, `extract_fortran`, `extract_go`, `extract_json`, `extract_markdown`, `extract_rust`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `_read_text()` (e.g. with `_get_c_func_name()` and `_import_c()`) actually correct?**
  _`_read_text()` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 44 inferred relationships involving `dispatch_command()` (e.g. with `format_affected()` and `god_nodes()`) actually correct?**
  _`dispatch_command()` has 44 INFERRED edges - model-reasoned connections that need verification._
- **Are the 51 inferred relationships involving `_make_id()` (e.g. with `extract_apex()` and `make_id()`) actually correct?**
  _`_make_id()` has 51 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `WebDataService` (e.g. with `_SuppressAssetsGetting` and `_SuppressQueuePolling`) actually correct?**
  _`WebDataService` has 4 INFERRED edges - model-reasoned connections that need verification._