package main

import (
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestLoadConfig(t *testing.T) {
	dir := t.TempDir()
	configPath := filepath.Join(dir, "config.toml")
	err := os.WriteFile(configPath, []byte(`
allowFile = ["allow_list.txt"]
allowURL = ["https://example.test/allow.txt"]
denyFile = ["block_list.txt"]
denyURL = ["https://example.test/deny.txt"]

[outputTXT]
enable = false
allow = "allow.txt"
deny = "deny.txt"

[outputJson]
enable = true
allow = "allow.json"
deny = "deny.json"

[outputAdGuard]
enable = true
file = "adguard.txt"
`), 0o644)
	if err != nil {
		t.Fatal(err)
	}

	cfg, err := loadConfig(configPath)
	if err != nil {
		t.Fatal(err)
	}

	if got, want := cfg.AllowFiles[0], "allow_list.txt"; got != want {
		t.Fatalf("allow file = %q, want %q", got, want)
	}
	if !cfg.OutputJSON.Enable || !cfg.OutputAdGuard.Enable {
		t.Fatal("expected JSON and AdGuard outputs to be enabled")
	}
}

func TestProcessLine(t *testing.T) {
	tests := []struct {
		name string
		line string
		want string
		ok   bool
	}{
		{name: "domain", line: " example.com ", want: "example.com", ok: true},
		{name: "empty", line: " ", ok: false},
		{name: "comment", line: "# example.com", ok: false},
		{name: "inline comment", line: "example.com # comment", ok: false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, ok := processLine(tt.line)
			if got != tt.want || ok != tt.ok {
				t.Fatalf("processLine(%q) = (%q, %v), want (%q, %v)", tt.line, got, ok, tt.want, tt.ok)
			}
		})
	}
}

func TestProcessRulesDeduplicatesSources(t *testing.T) {
	dir := t.TempDir()
	localPath := filepath.Join(dir, "rules.txt")
	if err := os.WriteFile(localPath, []byte("alpha.test\nbeta.test\nalpha.test\n"), 0o644); err != nil {
		t.Fatal(err)
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		_, _ = w.Write([]byte("beta.test\ngamma.test\n# comment\n"))
	}))
	defer server.Close()

	client := &http.Client{Timeout: time.Second}
	rules := processRules(client, []string{localPath, server.URL})

	if got, want := len(rules), 3; got != want {
		t.Fatalf("len(rules) = %d, want %d", got, want)
	}
	for _, rule := range []string{"alpha.test", "beta.test", "gamma.test"} {
		if _, ok := rules[rule]; !ok {
			t.Fatalf("missing rule %q", rule)
		}
	}
}
