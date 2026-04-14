// CJA Component Network - synthetic lab sample (Mean + 1.0 SD)
// Generated: 2026-04-14 11:30:28
// Components: 2 (0 Metrics, 1 Dimensions, 0 Calc Metrics, 1 Segments)
// Connections: 1
// Selection: Components > Mean + 1.0 * StdDev within each category
// Usage: summed co-usage counts from connections_sample_raw.json (illustrative only)

const nodes = [{"usage":475,"name":"Page name (lab)","id":"n1","type":"dimension","fullId":"variables/lab.dimension.page_name"},{"usage":475,"name":"Registered visitors (lab segment)","id":"n2","type":"segment","fullId":"s0FADEFADEFADEFADEFADEFAD@AdobeOrg_0000000000020001"}];
const apiConnections = [{"target":"n2","source":"n1","count":200}];
