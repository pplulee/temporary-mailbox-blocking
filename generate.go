package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

const batchSize = 4096

type config struct {
	AllowFiles []string
	AllowURLs  []string
	DenyFiles  []string
	DenyURLs   []string

	OutputTXT     textOutput
	OutputJSON    textOutput
	OutputAdGuard adguardOutput
}

type textOutput struct {
	Enable bool
	Allow  string
	Deny   string
}

type adguardOutput struct {
	Enable bool
	File   string
}

type sourceBatch struct {
	Lines []string
}

func main() {
	fmt.Println("Start generating rules...")
	fmt.Println()
	start := time.Now()

	cfg, err := loadConfig("config.toml")
	if err != nil {
		fail(err)
	}

	client := &http.Client{Timeout: 60 * time.Second}
	allowList := processRules(client, append(cfg.AllowURLs, cfg.AllowFiles...))
	denyList := processRules(client, append(cfg.DenyURLs, cfg.DenyFiles...))

	fmt.Printf("%d allow rules\n", len(allowList))
	fmt.Printf("%d deny rules\n", len(denyList))

	allowRules := sortedRules(allowList)
	denyRules := sortedRules(denyList)

	if cfg.OutputTXT.Enable {
		fmt.Printf("Output allow list to %s\n", cfg.OutputTXT.Allow)
		fmt.Printf("Output deny list to %s\n", cfg.OutputTXT.Deny)
		if err := writeLines(cfg.OutputTXT.Allow, allowRules); err != nil {
			fail(err)
		}
		if err := writeLines(cfg.OutputTXT.Deny, denyRules); err != nil {
			fail(err)
		}
	}

	if cfg.OutputJSON.Enable {
		fmt.Printf("Output allow list to %s\n", cfg.OutputJSON.Allow)
		fmt.Printf("Output deny list to %s\n", cfg.OutputJSON.Deny)
		if err := writeJSON(cfg.OutputJSON.Allow, allowRules); err != nil {
			fail(err)
		}
		if err := writeJSON(cfg.OutputJSON.Deny, denyRules); err != nil {
			fail(err)
		}
	}

	if cfg.OutputAdGuard.Enable {
		fmt.Printf("Output AdGuard rules to %s\n", cfg.OutputAdGuard.File)
		if err := writeAdGuard(cfg.OutputAdGuard.File, allowRules, denyRules); err != nil {
			fail(err)
		}
	}

	fmt.Println("\nDone")
	fmt.Printf("Time used: %s\n", time.Since(start))
}

func processRules(client *http.Client, sources []string) map[string]struct{} {
	rules := make(map[string]struct{})
	batches := make(chan sourceBatch, len(sources))

	var wg sync.WaitGroup
	for _, source := range sources {
		source := source
		wg.Add(1)
		go func() {
			defer wg.Done()
			processRuleSource(client, source, batches)
		}()
	}

	go func() {
		wg.Wait()
		close(batches)
	}()

	for batch := range batches {
		for _, line := range batch.Lines {
			rules[line] = struct{}{}
		}
	}

	return rules
}

func processRuleSource(client *http.Client, source string, batches chan<- sourceBatch) {
	var reader io.ReadCloser
	var err error

	if strings.HasPrefix(source, "http") {
		reader, err = getRuleFromURL(client, source)
	} else {
		reader, err = getRuleFromFile(source)
	}
	if err != nil {
		warn(err)
		return
	}
	defer reader.Close()

	scanner := bufio.NewScanner(reader)
	scanner.Buffer(make([]byte, 64*1024), 1024*1024)

	lines := make([]string, 0, batchSize)
	for scanner.Scan() {
		line, ok := processLine(scanner.Text())
		if !ok {
			continue
		}
		lines = append(lines, line)
		if len(lines) == batchSize {
			batches <- sourceBatch{Lines: lines}
			lines = make([]string, 0, batchSize)
		}
	}
	if len(lines) > 0 {
		batches <- sourceBatch{Lines: lines}
	}

	if err := scanner.Err(); err != nil {
		warn(fmt.Errorf("failed to read %s: %w", source, err))
	}
}

func getRuleFromURL(client *http.Client, url string) (io.ReadCloser, error) {
	resp, err := client.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to get %s: %w", url, err)
	}
	if resp.StatusCode != http.StatusOK {
		resp.Body.Close()
		return nil, fmt.Errorf("failed to get %s: HTTP %d", url, resp.StatusCode)
	}
	fmt.Printf("Reading %s...\n", url)
	return resp.Body, nil
}

func getRuleFromFile(filename string) (io.ReadCloser, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("%s not found: %w", filename, err)
	}
	fmt.Printf("Reading %s...\n", filename)
	return file, nil
}

func processLine(line string) (string, bool) {
	line = strings.TrimSpace(line)
	if line == "" || strings.Contains(line, "#") {
		return "", false
	}
	return line, true
}

func sortedRules(rules map[string]struct{}) []string {
	out := make([]string, 0, len(rules))
	for rule := range rules {
		out = append(out, rule)
	}
	sort.Strings(out)
	return out
}

func writeLines(filename string, lines []string) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	writer := bufio.NewWriter(file)
	for _, line := range lines {
		if _, err := writer.WriteString(line + "\n"); err != nil {
			return err
		}
	}
	return writer.Flush()
}

func writeJSON(filename string, lines []string) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	return json.NewEncoder(file).Encode(lines)
}

func writeAdGuard(filename string, allowRules, denyRules []string) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	writer := bufio.NewWriter(file)
	for _, line := range allowRules {
		if _, err := fmt.Fprintf(writer, "@@||%s^\n", line); err != nil {
			return err
		}
	}
	for _, line := range denyRules {
		if _, err := fmt.Fprintf(writer, "||%s^\n", line); err != nil {
			return err
		}
	}
	return writer.Flush()
}

func loadConfig(filename string) (config, error) {
	file, err := os.Open(filename)
	if err != nil {
		return config{}, err
	}
	defer file.Close()

	var cfg config
	section := ""
	scanner := bufio.NewScanner(file)
	lineNumber := 0
	for scanner.Scan() {
		lineNumber++
		line := strings.TrimSpace(stripComment(scanner.Text()))
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			section = strings.TrimSpace(line[1 : len(line)-1])
			continue
		}

		key, value, ok := strings.Cut(line, "=")
		if !ok {
			return cfg, fmt.Errorf("%s:%d: expected key = value", filename, lineNumber)
		}
		key = strings.TrimSpace(key)
		value = strings.TrimSpace(value)

		if err := applyConfigValue(&cfg, section, key, value); err != nil {
			return cfg, fmt.Errorf("%s:%d: %w", filename, lineNumber, err)
		}
	}
	if err := scanner.Err(); err != nil {
		return cfg, err
	}
	return cfg, nil
}

func applyConfigValue(cfg *config, section, key, value string) error {
	switch section {
	case "":
		items, err := parseStringArray(value)
		if err != nil {
			return err
		}
		switch key {
		case "allowFile":
			cfg.AllowFiles = items
		case "allowURL":
			cfg.AllowURLs = items
		case "denyFile":
			cfg.DenyFiles = items
		case "denyURL":
			cfg.DenyURLs = items
		default:
			return fmt.Errorf("unknown key %q", key)
		}
	case "outputTXT":
		return applyTextOutputValue(&cfg.OutputTXT, key, value)
	case "outputJson":
		return applyTextOutputValue(&cfg.OutputJSON, key, value)
	case "outputAdGuard":
		switch key {
		case "enable":
			enabled, err := strconv.ParseBool(value)
			if err != nil {
				return err
			}
			cfg.OutputAdGuard.Enable = enabled
		case "file":
			item, err := parseString(value)
			if err != nil {
				return err
			}
			cfg.OutputAdGuard.File = item
		default:
			return fmt.Errorf("unknown key %q in [%s]", key, section)
		}
	default:
		return fmt.Errorf("unknown section [%s]", section)
	}
	return nil
}

func applyTextOutputValue(output *textOutput, key, value string) error {
	switch key {
	case "enable":
		enabled, err := strconv.ParseBool(value)
		if err != nil {
			return err
		}
		output.Enable = enabled
	case "allow":
		item, err := parseString(value)
		if err != nil {
			return err
		}
		output.Allow = item
	case "deny":
		item, err := parseString(value)
		if err != nil {
			return err
		}
		output.Deny = item
	default:
		return fmt.Errorf("unknown key %q", key)
	}
	return nil
}

func parseStringArray(value string) ([]string, error) {
	value = strings.TrimSpace(value)
	if !strings.HasPrefix(value, "[") || !strings.HasSuffix(value, "]") {
		return nil, fmt.Errorf("expected string array, got %q", value)
	}

	body := strings.TrimSpace(value[1 : len(value)-1])
	if body == "" {
		return nil, nil
	}

	var items []string
	for _, part := range splitArrayItems(body) {
		item, err := parseString(strings.TrimSpace(part))
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, nil
}

func splitArrayItems(value string) []string {
	var items []string
	start := 0
	inString := false
	escaped := false

	for i, r := range value {
		switch {
		case escaped:
			escaped = false
		case r == '\\' && inString:
			escaped = true
		case r == '"':
			inString = !inString
		case r == ',' && !inString:
			items = append(items, value[start:i])
			start = i + 1
		}
	}
	items = append(items, value[start:])
	return items
}

func parseString(value string) (string, error) {
	value = strings.TrimSpace(value)
	item, err := strconv.Unquote(value)
	if err != nil {
		return "", fmt.Errorf("expected quoted string, got %q", value)
	}
	return item, nil
}

func stripComment(line string) string {
	inString := false
	escaped := false
	for i, r := range line {
		switch {
		case escaped:
			escaped = false
		case r == '\\' && inString:
			escaped = true
		case r == '"':
			inString = !inString
		case r == '#' && !inString:
			return line[:i]
		}
	}
	return line
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}

func warn(err error) {
	fmt.Fprintln(os.Stderr, err)
}
