// CJA Component Network - synthetic lab sample (above mean)
// Generated: 2026-04-14 11:31:53
// Components: 4 (1 Metrics, 1 Dimensions, 1 Calc Metrics, 1 Segments)
// Connections: 5
// Selection: Components above mean usage within each category
// Usage: summed co-usage counts from connections_sample_raw.json (illustrative only)

const nodes = [{"usage":475,"name":"Page name (lab)","id":"n1","type":"dimension","fullId":"variables/lab.dimension.page_name"},{"usage":423,"name":"Orders (lab)","id":"n2","type":"metric","fullId":"metrics/lab.metric.orders"},{"usage":113,"name":"Orders per visit (lab calc)","id":"n3","type":"calculatedMetric","fullId":"cm0FADEFADEFADEFADEFADEFAD@AdobeOrg_0000000000010001"},{"usage":475,"name":"Registered visitors (lab segment)","id":"n4","type":"segment","fullId":"s0FADEFADEFADEFADEFADEFAD@AdobeOrg_0000000000020001"}];
const apiConnections = [{"target":"n4","source":"n2","count":90},{"target":"n4","source":"n1","count":200},{"target":"n4","source":"n3","count":35},{"target":"n2","source":"n1","count":120},{"target":"n3","source":"n2","count":40}];
