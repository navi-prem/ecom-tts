package query

type struct QueryGenerator {}

func buildLuceneQuery(keywords []string) string {
    quoted := make([]string, 0, len(keywords))
    for _, k := range keywords {
        quoted = append(quoted, fmt.Sprintf("\"%s\"", k))
    }
    return strings.Join(quoted, " AND ")
}
