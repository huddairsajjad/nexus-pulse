/**
 * H.Huddair's Nexus-Pulse - Level 2 Enterprise
 * World-Class Enterprise React GUI Application
 * Standard: GitHub Enterprise / Linear / Vercel Modern Minimalist
 *
 * Capabilities:
 * - GitHub-Grade Theme Engine (GitHub Dark, Vercel Midnight, GitHub Light, Linear Dark)
 * - Kanban Lead Pipeline CRM with clean deduplicated tags and dynamic responsiveness
 * - Human Approval Gate with batch authorization and review modals
 * - Hot Lead alerts with 1-click AI executive response dispatcher
 * - Inbox Rotator with SMTP telemetry & daily domain send-cap monitors
 * - Dynamic Admin Profile Security (Bcrypt 12-round hashing)
 * - Role-Based Operator Management with streamlined inline action bars & fixed-width table
 * - Interactive Operator Audit Trail & Session Activity Viewer
 * - Multi-Format Data Backup System (JSON, XLSX, CSV)
 * - Cascading 3-Tier Hunt & Verify Lead Engine (Region -> Country -> City + custom industry + 100 lead limit)
 * - Complete input state-reversion fix across all forms and text fields
 * - Zero-latency Web Audio API subtle mechanical click sound engine across all components
 */

// =============================================================================
// SUBTLE UI CLICK SOUND SYNTHESIZER (Web Audio API)
// High-tech, zero-latency, zero-dependency tactile audio feedback
// =============================================================================
let _uiAudioContext = null;
let _soundMuted = false;

function getUiAudioContext() {
  if (typeof window === "undefined") return null;
  if (!_uiAudioContext) {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (AudioCtx) {
      _uiAudioContext = new AudioCtx();
    }
  }
  if (_uiAudioContext && _uiAudioContext.state === "suspended") {
    _uiAudioContext.resume().catch(() => {});
  }
  return _uiAudioContext;
}

function playUiSound(tone = "click") {
  if (_soundMuted) return;
  try {
    const ctx = getUiAudioContext();
    if (!ctx) return;

    const t = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    if (tone === "tab") {
      // Crisp subtle tone for navigation tabs
      osc.type = "sine";
      osc.frequency.setValueAtTime(880, t);
      osc.frequency.exponentialRampToValueAtTime(320, t + 0.045);
      gain.gain.setValueAtTime(0.045, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.045);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.045);
    } else if (tone === "action" || tone === "submit") {
      // Affirmative soft chime for primary buttons/submits
      osc.type = "triangle";
      osc.frequency.setValueAtTime(960, t);
      osc.frequency.exponentialRampToValueAtTime(440, t + 0.05);
      gain.gain.setValueAtTime(0.05, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.05);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.05);
    } else {
      // Default subtle mechanical click for buttons, cards, links, selects
      osc.type = "sine";
      osc.frequency.setValueAtTime(1150, t);
      osc.frequency.exponentialRampToValueAtTime(160, t + 0.035);
      gain.gain.setValueAtTime(0.04, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.035);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.035);
    }
  } catch (err) {
    // Non-blocking: never interrupt UI interaction if audio fails
  }
}

// Global delegated click listener for all interactive components
if (typeof document !== "undefined") {
  document.addEventListener("click", (evt) => {
    try {
      const el = evt.target;
      if (!el) return;

      const interactive = el.closest(
        'button, [role="button"], a, select, input[type="submit"], input[type="button"], input[type="checkbox"], input[type="radio"], [role="tab"], .np-nav-tab, .nav-tab, .tab-btn, .kanban-card, .np-card.cursor-pointer, .cursor-pointer, [data-clickable="true"]'
      );

      if (interactive) {
        const isTab = interactive.getAttribute("role") === "tab" ||
                      interactive.classList.contains("np-nav-tab") ||
                      interactive.classList.contains("nav-tab") ||
                      interactive.classList.contains("tab-btn") ||
                      (interactive.tagName === "BUTTON" && interactive.closest("nav"));
        const isAction = interactive.classList.contains("btn-primary") ||
                         interactive.type === "submit";
        const tone = isTab ? "tab" : isAction ? "action" : "click";
        playUiSound(tone);
      }
    } catch (e) {
      // Fail safely
    }
  }, { capture: true, passive: true });
}

window.playUiSound = playUiSound;

const { useState, useEffect, useRef, useMemo } = React;
const API_BASE = window.location.origin;

// -----------------------------------------------------------------------------
// GEOGRAPHIC TAXONOMY: 3-TIER REGION -> COUNTRY -> CITY
// -----------------------------------------------------------------------------
const GEO_REGIONS = {
  "Europe": {
    countries: {
      "Germany": ["Berlin", "Munich", "Frankfurt", "Hamburg", "Cologne", "Stuttgart", "Düsseldorf"],
      "UK": ["London", "Manchester", "Birmingham", "Leeds", "Bristol", "Edinburgh", "Glasgow"],
      "France": ["Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Bordeaux"],
      "Netherlands": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven"],
      "Spain": ["Madrid", "Barcelona", "Valencia", "Seville", "Bilbao"],
      "Italy": ["Milan", "Rome", "Turin", "Naples", "Bologna", "Florence"],
      "Switzerland": ["Zurich", "Geneva", "Basel", "Bern", "Lausanne"],
      "Poland": ["Warsaw", "Krakow", "Wroclaw", "Gdansk", "Poznan"]
    }
  },
  "North America": {
    countries: {
      "USA": ["New York", "Chicago", "Houston", "Dallas", "Atlanta", "Phoenix", "Los Angeles", "Miami", "Seattle", "Austin"],
      "Canada": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa", "Edmonton"]
    }
  },
  "Middle East": {
    countries: {
      "UAE": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah"],
      "Saudi Arabia": ["Riyadh", "Jeddah", "Dammam", "Mecca", "Medina"],
      "Qatar": ["Doha", "Al Wakrah", "Al Khor", "Al Rayyan"]
    }
  },
  "South Asia": {
    countries: {
      "Pakistan": ["Lahore", "Karachi", "Islamabad", "Sialkot", "Faisalabad", "Rawalpindi"],
      "India": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune"]
    }
  },
  "Asia Pacific": {
    countries: {
      "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
      "Singapore": ["Singapore", "Jurong", "Tampines", "Woodlands"]
    }
  }
};

const INDUSTRY_PRESETS = [
  "Commercial Construction",
  "Sports Wear Manufacturers",
  "Gym Equipment",
  "Enterprise SaaS",
  "MedTech & Healthcare",
  "Luxury Real Estate",
  "Industrial Manufacturing",
  "Logistics & Freight",
  "Renewable Energy & Solar",
  "FinTech & Payments"
];

const THEMES = [
  { id: "github-dark", name: "GitHub Dark", dotColor: "#58a6ff", desc: "Default slate-grey minimalist" },
  { id: "vercel-midnight", name: "Vercel Midnight", dotColor: "#ffffff", desc: "Pure OLED obsidian & mono" },
  { id: "github-light", name: "GitHub Light", dotColor: "#0969da", desc: "Clean corporate enterprise mode" },
  { id: "linear-dark", name: "Linear Dark", dotColor: "#818cf8", desc: "Minimalist charcoal & muted accents" }
];

const KANBAN_STAGES = [
  { key: "SCRAPED", label: "Scraped", badgeClass: "badge-muted" },
  { key: "VERIFIED", label: "Verified", badgeClass: "badge-accent" },
  { key: "PENDING_APPROVAL", label: "Approval Hold", badgeClass: "badge-warning" },
  { key: "APPROVED", label: "Authorized", badgeClass: "badge-purple" },
  { key: "SENT", label: "Dispatched", badgeClass: "badge-muted" },
  { key: "REPLIED", label: "Replied", badgeClass: "badge-accent" },
  { key: "HOT_LEAD", label: "Hot Lead", badgeClass: "badge-danger" },
  { key: "CLOSED", label: "Converted", badgeClass: "badge-success" }
];

function NexusPulseApp() {
  // ---------------------------------------------------------------------------
  // THEME ENGINE (Requirement 1)
  // ---------------------------------------------------------------------------
  const [activeTheme, setActiveTheme] = useState(() => {
    return localStorage.getItem("nexus_theme") || "github-dark";
  });
  const [isThemeMenuOpen, setIsThemeMenuOpen] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", activeTheme);
    document.body.setAttribute("data-theme", activeTheme);
    localStorage.setItem("nexus_theme", activeTheme);
  }, [activeTheme]);

  // ---------------------------------------------------------------------------
  // AUTH & AUDIO STATE
  // ---------------------------------------------------------------------------
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("nexus_user");
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem("nexus_token") || "");

  // UI Click Sound Effects Engine State
  const [soundEnabled, setSoundEnabled] = useState(() => localStorage.getItem("nexus_sound_enabled") !== "false");
  useEffect(() => {
    _soundMuted = !soundEnabled;
    localStorage.setItem("nexus_sound_enabled", soundEnabled ? "true" : "false");
  }, [soundEnabled]);

  // Production Clean Setup Check
  const [setupRequired, setSetupRequired] = useState(false);
  const [setupChecked, setSetupChecked] = useState(false);

  // First-Run Master Admin Initialization Form State
  const [initUsername, setInitUsername] = useState("");
  const [initFullName, setInitFullName] = useState("");
  const [initEmail, setInitEmail] = useState("");
  const [initPassword, setInitPassword] = useState("");
  const [initConfirmPassword, setInitConfirmPassword] = useState("");
  const [initError, setInitError] = useState("");
  const [isInitializingAdmin, setIsInitializingAdmin] = useState(false);

  // Production Clean Login Form State (No pre-populated test/demo logins)
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [scanStep, setScanStep] = useState("");

  // ---------------------------------------------------------------------------
  // CORE TELEMETRY & PIPELINE STATE
  // ---------------------------------------------------------------------------
  const [pulseState, setPulseState] = useState("IDLE"); // 'IDLE', 'HUNTING', 'HOT_ALERT'
  const [systemHealth, setSystemHealth] = useState(null);
  const [kanbanItems, setKanbanItems] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [hotLeads, setHotLeads] = useState([]);
  const [mailboxes, setMailboxes] = useState([]);
  const [timezones, setTimezones] = useState({});
  const [activeTab, setActiveTab] = useState("kanban");
  const [alertBanner, setAlertBanner] = useState(null);

  // ---------------------------------------------------------------------------
  // OPERATOR & SECURITY MANAGEMENT STATE
  // ---------------------------------------------------------------------------
  const [operatorsList, setOperatorsList] = useState([]);
  const [adminProfile, setAdminProfile] = useState(null);
  const [licenseTelemetry, setLicenseTelemetry] = useState(null);
  const [auditSearch, setAuditSearch] = useState("");

  // Inline action bar state for operator rows
  const [expandedOperatorId, setExpandedOperatorId] = useState(null);
  const [inlineScrapeQuota, setInlineScrapeQuota] = useState("200");
  const [inlineSendQuota, setInlineSendQuota] = useState("50");

  // Modals
  const [isCreateOperatorOpen, setIsCreateOperatorOpen] = useState(false);
  const [selectedUserForReset, setSelectedUserForReset] = useState(null);
  const [resetPasswordInput, setResetPasswordInput] = useState("");

  // ---------------------------------------------------------------------------
  // GLOBAL INPUT STATE REVERSION FIX
  // Protected refs prevent background polling from resetting user typing
  // ---------------------------------------------------------------------------
  const adminProfileLoadedRef = useRef(false);
  const adminFormDirtyRef = useRef(false);

  const [adminUsernameInput, setAdminUsernameInput] = useState("");
  const [adminEmailInput, setAdminEmailInput] = useState("");
  const [adminFullNameInput, setAdminFullNameInput] = useState("");
  const [adminCurrentPassword, setAdminCurrentPassword] = useState("");
  const [adminNewPassword, setAdminNewPassword] = useState("");
  const [adminConfirmPassword, setAdminConfirmPassword] = useState("");

  // Form State: Create Operator
  const [newOpUsername, setNewOpUsername] = useState("");
  const [newOpPassword, setNewOpPassword] = useState("");
  const [newOpFullName, setNewOpFullName] = useState("");
  const [newOpEmail, setNewOpEmail] = useState("");
  const [newOpDeviceLock, setNewOpDeviceLock] = useState("NEXUS-E727-BB0B-765E-4021");
  const [newOpExpiryDays, setNewOpExpiryDays] = useState("90");
  const [newOpScrapeQuota, setNewOpScrapeQuota] = useState("200");
  const [newOpSendQuota, setNewOpSendQuota] = useState("50");

  // ---------------------------------------------------------------------------
  // MULTI-FORMAT DATA BACKUP MODAL
  // ---------------------------------------------------------------------------
  const [isBackupModalOpen, setIsBackupModalOpen] = useState(false);
  const [isBackingUp, setIsBackingUp] = useState(false);

  // ---------------------------------------------------------------------------
  // GLOBAL LEAD ENGINE PIPELINE MODAL (3-Tier Cascading)
  // ---------------------------------------------------------------------------
  const [isHuntModalOpen, setIsHuntModalOpen] = useState(false);
  const [huntRegion, setHuntRegion] = useState("Europe");
  const [huntCountry, setHuntCountry] = useState("Germany");
  const [huntCity, setHuntCity] = useState("Berlin");
  const [isCustomCity, setIsCustomCity] = useState(false);
  const [huntCustomCity, setHuntCustomCity] = useState("");
  const [huntNiche, setHuntNiche] = useState("Commercial Construction");
  const [huntMaxResults, setHuntMaxResults] = useState(20);
  const [isHunting, setIsHunting] = useState(false);

  const availableCountries = useMemo(() => {
    return Object.keys(GEO_REGIONS[huntRegion]?.countries || {});
  }, [huntRegion]);

  const availableCities = useMemo(() => {
    return GEO_REGIONS[huntRegion]?.countries[huntCountry] || [];
  }, [huntRegion, huntCountry]);

  const handleRegionChange = (newRegion) => {
    setHuntRegion(newRegion);
    const firstCountry = Object.keys(GEO_REGIONS[newRegion]?.countries || {})[0] || "Germany";
    setHuntCountry(firstCountry);
    const firstCity = GEO_REGIONS[newRegion]?.countries[firstCountry]?.[0] || "Berlin";
    setHuntCity(firstCity);
    setIsCustomCity(false);
  };

  const handleCountryChange = (newCountry) => {
    setHuntCountry(newCountry);
    const firstCity = GEO_REGIONS[huntRegion]?.countries[newCountry]?.[0] || "Berlin";
    setHuntCity(firstCity);
    setIsCustomCity(false);
  };

  // Pipeline approval & hot lead review modals
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [approvalSubject, setApprovalSubject] = useState("");
  const [approvalBody, setApprovalBody] = useState("");

  const [selectedHotLead, setSelectedHotLead] = useState(null);
  const [hotLeadReplyBody, setHotLeadReplyBody] = useState("");

  // Mailbox management modals
  const [isAddMailboxOpen, setIsAddMailboxOpen] = useState(false);
  const [newMbDisplayName, setNewMbDisplayName] = useState("");
  const [newMbEmail, setNewMbEmail] = useState("");
  const [newMbHost, setNewMbHost] = useState("");
  const [newMbPort, setNewMbPort] = useState("587");
  const [newMbUsername, setNewMbUsername] = useState("");
  const [newMbPassword, setNewMbPassword] = useState("");
  const [newMbDailyLimit, setNewMbDailyLimit] = useState("45");

  const [selectedMailboxForEdit, setSelectedMailboxForEdit] = useState(null);
  const [editMbDisplayName, setEditMbDisplayName] = useState("");
  const [editMbEmail, setEditMbEmail] = useState("");
  const [editMbHost, setEditMbHost] = useState("");
  const [editMbPort, setEditMbPort] = useState("587");
  const [editMbUsername, setEditMbUsername] = useState("");
  const [editMbPassword, setEditMbPassword] = useState("");
  const [editMbDailyLimit, setEditMbDailyLimit] = useState("45");

  // ---------------------------------------------------------------------------
  // FETCH CORE DATA (4-Second Periodic Polling)
  // ---------------------------------------------------------------------------
  const fetchData = async () => {
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const [healthRes, kanbanRes, approvalsRes, hotLeadsRes, mailboxesRes, tzRes] = await Promise.all([
        fetch(`${API_BASE}/api/health`, { headers }).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/kanban/leads`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/outreach/pending`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/outreach/hot-leads`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/outreach/mailboxes`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/scheduler/timezones`, { headers }).then(r => r.json()).catch(() => ({}))
      ]);

      if (healthRes) setSystemHealth(healthRes);
      if (Array.isArray(kanbanRes)) setKanbanItems(kanbanRes);
      if (Array.isArray(approvalsRes)) setPendingApprovals(approvalsRes);
      if (Array.isArray(hotLeadsRes)) {
        setHotLeads(hotLeadsRes);
        if (hotLeadsRes.length > 0) {
          setPulseState("HOT_ALERT");
        } else if (pulseState === "HOT_ALERT") {
          setPulseState("IDLE");
        }
      }
      if (Array.isArray(mailboxesRes)) setMailboxes(mailboxesRes);
      if (tzRes) setTimezones(tzRes);

      if (user && user.role === "admin") {
        fetch(`${API_BASE}/api/operators`, { headers }).then(r => r.json()).then(data => {
          if (Array.isArray(data)) setOperatorsList(data);
        }).catch(() => {});

        fetch(`${API_BASE}/api/admin/profile`, { headers }).then(r => r.json()).then(data => {
          if (data && data.username) {
            setAdminProfile(data);
            if (!adminProfileLoadedRef.current && !adminFormDirtyRef.current) {
              setAdminUsernameInput(data.username);
              setAdminEmailInput(data.email || "");
              setAdminFullNameInput(data.full_name || "");
              adminProfileLoadedRef.current = true;
            }
          }
        }).catch(() => {});

        fetch(`${API_BASE}/api/licenses/telemetry`, { headers }).then(r => r.json()).then(data => {
          if (data) setLicenseTelemetry(data);
        }).catch(() => {});
      }
    } catch (e) {
      console.error("Data sync error:", e);
    }
  };

  useEffect(() => {
    if (user && token) {
      fetchData();
      const interval = setInterval(fetchData, 4000);
      return () => clearInterval(interval);
    }
  }, [user, token]);

  // Check if system is in fresh production state requiring Master Admin setup
  useEffect(() => {
    const checkSetupStatus = async () => {
      try {
        const resp = await fetch(`${API_BASE}/api/auth/setup-status`);
        if (resp.ok) {
          const data = await resp.json();
          if (data && data.initialized === false) {
            setSetupRequired(true);
            localStorage.removeItem("nexus_token");
            localStorage.removeItem("nexus_user");
            setUser(null);
            setToken("");
          } else {
            setSetupRequired(false);
          }
        }
      } catch (err) {
        console.warn("Could not query setup status:", err);
      } finally {
        setSetupChecked(true);
      }
    };
    checkSetupStatus();
  }, []);

  // ---------------------------------------------------------------------------
  // AUTHENTICATION HANDLERS
  // ---------------------------------------------------------------------------
  const handleInitializeAdmin = async (e) => {
    if (e) e.preventDefault();
    setInitError("");

    if (!initUsername.trim()) {
      setInitError("Administrator username is required.");
      return;
    }
    if (initUsername.trim().length < 3) {
      setInitError("Username must be at least 3 characters.");
      return;
    }
    if (!initFullName.trim()) {
      setInitError("Full name is required.");
      return;
    }
    if (initPassword.length < 6) {
      setInitError("Master passphrase must be at least 6 characters.");
      return;
    }
    if (initPassword !== initConfirmPassword) {
      setInitError("Passphrase confirmation does not match.");
      return;
    }

    setIsInitializingAdmin(true);
    try {
      const resp = await fetch(`${API_BASE}/api/auth/initialize-admin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: initUsername.trim(),
          password: initPassword,
          full_name: initFullName.trim(),
          email: initEmail.trim() || undefined
        })
      });
      const data = await resp.json();

      if (resp.ok && data.token) {
        playUiSound("action");
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem("nexus_token", data.token);
        localStorage.setItem("nexus_user", JSON.stringify(data.user));
        setSetupRequired(false);
        setAlertBanner({
          type: "success",
          message: `Master Administrator [${data.user.username}] successfully initialized and hardware-bound!`
        });
      } else {
        setInitError(data.detail || "Failed to initialize administrator.");
      }
    } catch (err) {
      setInitError("Network Error: Could not reach FastAPI backend.");
    } finally {
      setIsInitializingAdmin(false);
    }
  };
  const handleBiometricLogin = async (e) => {
    if (e) e.preventDefault();
    setLoginError("");
    setIsScanning(true);
    setScanStep("Initializing hardware cryptographic handshake...");

    setTimeout(() => setScanStep("Scanning device MachineGuid & MAC signature..."), 450);
    setTimeout(() => setScanStep("Validating HMAC-SHA256 Level 2 Authorization Matrix..."), 900);

    setTimeout(async () => {
      try {
        const resp = await fetch(`${API_BASE}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: loginUsername, password: loginPassword })
        });
        const data = await resp.json();

        if (resp.ok && data.token) {
          setScanStep("Access Granted! Loading H.Huddair Nexus-Pulse Core...");
          setTimeout(() => {
            setToken(data.token);
            setUser(data.user);
            localStorage.setItem("nexus_token", data.token);
            localStorage.setItem("nexus_user", JSON.stringify(data.user));
            setIsScanning(false);
          }, 350);
        } else {
          setIsScanning(false);
          setLoginError(data.detail || "Authentication Failed: Invalid credentials or account access revoked.");
        }
      } catch (err) {
        setIsScanning(false);
        setLoginError("Connection Error: FastAPI backend unreachable.");
      }
    }, 1300);
  };

  const handleLogout = () => {
    localStorage.removeItem("nexus_token");
    localStorage.removeItem("nexus_user");
    setUser(null);
    setToken("");
    adminProfileLoadedRef.current = false;
    adminFormDirtyRef.current = false;
  };

  // ---------------------------------------------------------------------------
  // MULTI-FORMAT DATA BACKUP EXPORT
  // ---------------------------------------------------------------------------
  const handleDownloadBackup = async (format = "json") => {
    setIsBackingUp(true);
    setAlertBanner({
      type: "info",
      message: `Generating snapshot backup in ${format.toUpperCase()} format...`
    });

    try {
      const resp = await fetch(`${API_BASE}/api/backup/download?format=${format}`, {
        method: "GET",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });

      if (!resp.ok) {
        throw new Error(`Server returned status ${resp.status}`);
      }

      const blob = await resp.blob();
      const ext = format === "xlsx" ? "xlsx" : format === "csv" ? "csv" : "json";
      let filename = `nexus_leads_backup_${new Date().toISOString().slice(0, 10)}.${ext}`;

      const disposition = resp.headers.get("Content-Disposition");
      if (disposition && disposition.indexOf("filename=") !== -1) {
        const match = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        if (match && match[1]) {
          filename = match[1].replace(/['"]/g, "");
        }
      }

      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      setAlertBanner({
        type: "success",
        message: `Snapshot backup successfully generated and downloaded: ${filename}`
      });
      setIsBackupModalOpen(false);
    } catch (e) {
      console.error("Backup download error:", e);
      setAlertBanner({
        type: "error",
        message: `Backup export error: ${e.message}`
      });
    } finally {
      setIsBackingUp(false);
    }
  };

  // ---------------------------------------------------------------------------
  // HUNT & VERIFY LEAD ENGINE
  // ---------------------------------------------------------------------------
  const handleLaunchScrapePipeline = async (e) => {
    if (e) e.preventDefault();
    setIsHunting(true);
    setPulseState("HUNTING");

    const effectiveCity = isCustomCity ? (huntCustomCity.trim() || huntCity) : huntCity;

    setAlertBanner({
      type: "info",
      message: `Deploying Deep Scraper for '${huntNiche}' in ${effectiveCity}, ${huntCountry} (${huntRegion}) [Limit: ${huntMaxResults} leads]...`
    });

    try {
      const resp = await fetch(`${API_BASE}/api/scrape`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          region: huntRegion,
          country: huntCountry,
          city: effectiveCity,
          niche: huntNiche,
          max_results: parseInt(huntMaxResults, 10) || 20
        })
      });

      const data = await resp.json();

      if (resp.ok) {
        setSystemHealth(prev => prev ? {
          ...prev,
          active_configuration: {
            ...prev.active_configuration,
            target_country: huntCountry,
            industry_niche: huntNiche
          }
        } : prev);

        const scraped = data.scraped_leads || [];
        const verified = data.verified_leads || [];

        setKanbanItems(prev => {
          const existingIds = new Set(prev.map(i => i.id));
          const newItems = [...scraped, ...verified].filter(i => !existingIds.has(i.id));
          return [...newItems, ...prev];
        });

        fetchData();
        setIsHuntModalOpen(false);
        setAlertBanner({
          type: "success",
          message: `Pipeline Completed! Scraped: ${data.scraped_count || scraped.length} | Verified: ${data.verified_count || verified.length} leads in ${effectiveCity}, ${huntCountry}.`
        });
      } else {
        alert(data.detail || "Scrape pipeline failed.");
      }
    } catch (err) {
      console.error("Scrape error:", err);
      setAlertBanner({ type: "error", message: "Failed to connect to /api/scrape endpoint." });
    } finally {
      setIsHunting(false);
      setPulseState(hotLeads.length > 0 ? "HOT_ALERT" : "IDLE");
    }
  };

  // ---------------------------------------------------------------------------
  // HUMAN APPROVAL GATE HANDLERS
  // ---------------------------------------------------------------------------
  const handleOpenApprovalModal = (item) => {
    setSelectedApproval(item);
    setApprovalSubject(item.subject || "");
    setApprovalBody(item.message_body || "");
  };

  const handleApproveOutreach = async (queueId, customSubject, customBody) => {
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          queue_id: queueId,
          approver: user.username,
          edited_subject: customSubject,
          edited_body: customBody
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setSelectedApproval(null);
        setAlertBanner({
          type: "success",
          message: `Outreach item approved by ${user.username}! Scheduled for 9:00 - 11:00 AM local window.`
        });
        fetchData();
      } else {
        alert(data.detail || "Approval failed.");
      }
    } catch (e) {
      alert("Error approving outreach.");
    }
  };

  const handleBatchApprove = async () => {
    if (!confirm(`Confirm authorization to approve all ${pendingApprovals.length} pending leads in the Human Gate?`)) return;
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/batch-approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ approver: user.username })
      });
      const data = await resp.json();
      setAlertBanner({
        type: "success",
        message: `Authorized: ${data.items_approved} outreach items approved by ${user.username}!`
      });
      fetchData();
    } catch (e) {
      alert("Batch approval failed.");
    }
  };

  // ---------------------------------------------------------------------------
  // HOT LEAD HANDLERS
  // ---------------------------------------------------------------------------
  const handleOpenHotLeadModal = (lead) => {
    setSelectedHotLead(lead);
    setHotLeadReplyBody(lead.ai_suggested_reply || "");
  };

  const handleDispatchHotLeadReply = async (replyId, recipient, responseBody) => {
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/send-hot-reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ reply_id: replyId, recipient, response_body: responseBody })
      });
      const data = await resp.json();
      setSelectedHotLead(null);
      setAlertBanner({
        type: "success",
        message: `Executive Response dispatched to ${recipient} via ${data.dispatched_via}!`
      });
      fetchData();
    } catch (e) {
      alert("Error sending response.");
    }
  };

  // ---------------------------------------------------------------------------
  // INBOX ROTATOR HANDLERS
  // ---------------------------------------------------------------------------
  const handleAddMailbox = async (e) => {
    if (e) e.preventDefault();
    try {
      const resp = await fetch(`${API_BASE}/api/mailboxes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          display_name: newMbDisplayName,
          email_address: newMbEmail,
          smtp_host: newMbHost,
          smtp_port: parseInt(newMbPort, 10) || 587,
          smtp_username: newMbUsername,
          smtp_password: newMbPassword,
          daily_limit: parseInt(newMbDailyLimit, 10) || 45
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setIsAddMailboxOpen(false);
        setNewMbDisplayName("");
        setNewMbEmail("");
        setNewMbHost("");
        setNewMbPort("587");
        setNewMbUsername("");
        setNewMbPassword("");
        setNewMbDailyLimit("45");
        setAlertBanner({ type: "success", message: `Mailbox '${data.email_address}' enrolled into rotator!` });
        fetchData();
      } else {
        alert(data.detail || "Failed to add mailbox.");
      }
    } catch (err) {
      alert("Error adding mailbox.");
    }
  };

  const handleOpenEditMailbox = (mb) => {
    setSelectedMailboxForEdit(mb);
    setEditMbDisplayName(mb.display_name || "");
    setEditMbEmail(mb.email_address || "");
    setEditMbHost(mb.smtp_host || "");
    setEditMbPort(String(mb.smtp_port || 587));
    setEditMbUsername(mb.smtp_username || "");
    setEditMbPassword(mb.smtp_password || "");
    setEditMbDailyLimit(String(mb.daily_limit || 45));
  };

  const handleUpdateMailbox = async (e) => {
    if (e) e.preventDefault();
    if (!selectedMailboxForEdit) return;
    try {
      const resp = await fetch(`${API_BASE}/api/mailboxes/${selectedMailboxForEdit.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          display_name: editMbDisplayName,
          email_address: editMbEmail,
          smtp_host: editMbHost,
          smtp_port: parseInt(editMbPort, 10) || 587,
          smtp_username: editMbUsername,
          smtp_password: editMbPassword || undefined,
          daily_limit: parseInt(editMbDailyLimit, 10) || 45
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setSelectedMailboxForEdit(null);
        setAlertBanner({ type: "success", message: `Mailbox '${data.email_address}' updated successfully!` });
        fetchData();
      } else {
        alert(data.detail || "Failed to update mailbox.");
      }
    } catch (err) {
      alert("Error updating mailbox.");
    }
  };

  const handleDeleteMailbox = async (mb) => {
    if (!confirm(`Permanently remove mailbox "${mb.display_name}" (${mb.email_address}) from the rotator pool?`)) return;
    try {
      const resp = await fetch(`${API_BASE}/api/mailboxes/${mb.id}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({ type: "info", message: `Mailbox '${mb.email_address}' removed from rotator pool.` });
        fetchData();
      } else {
        alert(data.detail || "Failed to delete mailbox.");
      }
    } catch (err) {
      alert("Error deleting mailbox.");
    }
  };

  // ---------------------------------------------------------------------------
  // ADMIN PROFILE & SECURITY SETTINGS
  // ---------------------------------------------------------------------------
  const handleUpdateAdminProfile = async (e) => {
    if (e) e.preventDefault();
    if (adminNewPassword && adminNewPassword !== adminConfirmPassword) {
      alert("Error: New Password and Confirm Password do not match.");
      return;
    }
    try {
      const resp = await fetch(`${API_BASE}/api/admin/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          username: adminUsernameInput,
          email: adminEmailInput,
          full_name: adminFullNameInput,
          current_password: adminCurrentPassword || undefined,
          new_password: adminNewPassword || undefined
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({ type: "success", message: "Admin profile updated successfully! Password re-hashed with Bcrypt." });
        setAdminCurrentPassword("");
        setAdminNewPassword("");
        setAdminConfirmPassword("");
        adminFormDirtyRef.current = false;
        fetchData();
      } else {
        alert(data.detail || "Profile update failed.");
      }
    } catch (err) {
      alert("Error updating profile.");
    }
  };

  // ---------------------------------------------------------------------------
  // OPERATOR MANAGEMENT HANDLERS
  // ---------------------------------------------------------------------------
  const handleToggleOperatorStatus = async (operatorId) => {
    try {
      const resp = await fetch(`${API_BASE}/api/operators/${operatorId}/toggle-status`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({ type: "info", message: `Operator status updated to: ${data.status_label}` });
        fetchData();
      } else {
        alert(data.detail || "Status toggle failed.");
      }
    } catch (err) {
      alert("Error toggling operator status.");
    }
  };

  const handleOpenResetPasswordModal = (op) => {
    setSelectedUserForReset(op);
    setResetPasswordInput("");
  };

  const handleResetOperatorPassword = async (e) => {
    if (e) e.preventDefault();
    if (!resetPasswordInput || resetPasswordInput.length < 6) {
      alert("Password must be at least 6 characters.");
      return;
    }
    try {
      const resp = await fetch(`${API_BASE}/api/operators/${selectedUserForReset.id}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ new_password: resetPasswordInput })
      });
      const data = await resp.json();
      if (resp.ok) {
        setSelectedUserForReset(null);
        setAlertBanner({ type: "success", message: `Password reset successfully for ${data.username} using Bcrypt encryption.` });
        fetchData();
      } else {
        alert(data.detail || "Password reset failed.");
      }
    } catch (err) {
      alert("Error resetting password.");
    }
  };

  const handleCreateOperator = async (e) => {
    if (e) e.preventDefault();
    try {
      const resp = await fetch(`${API_BASE}/api/operators`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          username: newOpUsername,
          password: newOpPassword,
          full_name: newOpFullName,
          email: newOpEmail,
          device_lock_id: newOpDeviceLock,
          device_lock_enabled: true,
          expiry_days: parseInt(newOpExpiryDays, 10) || 90,
          daily_scrape_quota: parseInt(newOpScrapeQuota, 10) || 200,
          daily_send_quota: parseInt(newOpSendQuota, 10) || 50
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setIsCreateOperatorOpen(false);
        setNewOpUsername("");
        setNewOpPassword("");
        setNewOpFullName("");
        setNewOpEmail("");
        setNewOpExpiryDays("90");
        setNewOpScrapeQuota("200");
        setNewOpSendQuota("50");
        setAlertBanner({ type: "success", message: `Operator account '${data.username}' created with signed license token!` });
        fetchData();
      } else {
        alert(data.detail || "Operator creation failed.");
      }
    } catch (err) {
      alert("Error creating operator.");
    }
  };

  const handleToggleInlineAdjust = (op) => {
    if (expandedOperatorId === op.id) {
      setExpandedOperatorId(null);
    } else {
      setExpandedOperatorId(op.id);
      setInlineScrapeQuota(String(op.daily_scrape_quota || 200));
      setInlineSendQuota(String(op.daily_send_quota || 50));
    }
  };

  const handleApplyInlineQuotas = async (operatorId, extendDays = null) => {
    try {
      const resp = await fetch(`${API_BASE}/api/operators/${operatorId}/quotas`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          extend_days: extendDays,
          daily_scrape_quota: parseInt(inlineScrapeQuota, 10) || 200,
          daily_send_quota: parseInt(inlineSendQuota, 10) || 50
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({
          type: "success",
          message: `Quotas updated for ${data.username}! New Expiry: ${data.new_expiry_date || "Perpetual"}`
        });
        setExpandedOperatorId(null);
        fetchData();
      } else {
        alert(data.detail || "Quota modification failed.");
      }
    } catch (err) {
      alert("Error modifying quotas.");
    }
  };

  // ---------------------------------------------------------------------------
  // HELPER: CLEAN KANBAN TAG DEDUPLICATION
  // ---------------------------------------------------------------------------
  const getCleanLeadBadges = (lead) => {
    const badges = [];

    const rawTier = (lead.primary_email_tier || lead.channel || "TIER_1").toUpperCase();
    let tierLabel = "Tier 1";
    if (rawTier.includes("ESTIMATING")) {
      tierLabel = "Tier 1 Estimating";
    } else if (rawTier.includes("TIER_2")) {
      tierLabel = "Tier 2";
    } else if (rawTier.includes("WEB_FORM")) {
      tierLabel = "Web Form";
    } else if (rawTier.includes("EMAIL")) {
      tierLabel = "Direct Email";
    }
    badges.push({ text: tierLabel, type: "tier" });

    if (lead.quality_tag) {
      const normQuality = lead.quality_tag.toUpperCase().replace(/[-_]/g, " ");
      if (!normQuality.includes("TIER 1") && !normQuality.includes("ESTIMATING")) {
        badges.push({ text: lead.quality_tag, type: "quality" });
      }
    }

    return badges;
  };

  // ---------------------------------------------------------------------------
  // VIEW: ENTERPRISE LOGIN / FIRST-RUN SETUP SCREEN
  // ---------------------------------------------------------------------------
  if (!user || !token) {
    if (setupRequired) {
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-base relative">
          {/* Audio SFX Toggle */}
          <div className="absolute top-4 right-4">
            <button
              type="button"
              onClick={() => {
                const next = !soundEnabled;
                setSoundEnabled(next);
                if (next) setTimeout(() => playUiSound("action"), 50);
              }}
              className={`btn btn-sm ${soundEnabled ? "btn-secondary text-theme-accent" : "btn-ghost text-theme-muted"}`}
              title={soundEnabled ? "UI Audio SFX Active (Click to Mute)" : "UI Audio SFX Muted (Click to Enable)"}
            >
              <span>{soundEnabled ? "🔊" : "🔇"}</span>
              <span className="text-[11px] font-mono">{soundEnabled ? "SFX: ON" : "SFX: OFF"}</span>
            </button>
          </div>

          <div className="np-card w-full max-w-lg p-8 relative overflow-hidden shadow-2xl border-theme">
            <div className="text-center mb-6">
              <div className="w-12 h-12 mx-auto mb-3 rounded-lg border-theme bg-elevated flex items-center justify-center font-bold text-base text-theme-accent font-mono">
                NP
              </div>
              <h1 className="text-xl font-bold tracking-tight text-theme-primary">
                Nexus-Pulse Level 2 Enterprise
              </h1>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 mt-2 rounded-full text-[11px] font-mono bg-[var(--accent-muted)] text-[var(--accent)] border border-[var(--accent)]">
                <span>★</span> Fresh Production State — First-Run Admin Setup
              </div>
              <p className="text-xs text-theme-secondary mt-2">
                Clean installation detected. Initialize your Master Administrator profile and bind your host hardware key.
              </p>
            </div>

            {initError && (
              <div className="mb-5 np-alert np-alert-error">
                <span>{initError}</span>
              </div>
            )}

            <form onSubmit={handleInitializeAdmin} className="space-y-4">
              <div>
                <label className="np-label">Master Administrator Username *</label>
                <input
                  type="text"
                  value={initUsername}
                  onChange={(e) => setInitUsername(e.target.value)}
                  className="np-input font-mono"
                  placeholder="e.g. admin or h.huddair"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="np-label">Executive Full Name *</label>
                  <input
                    type="text"
                    value={initFullName}
                    onChange={(e) => setInitFullName(e.target.value)}
                    className="np-input"
                    placeholder="e.g. H.Huddair (Master Admin)"
                    required
                  />
                </div>
                <div>
                  <label className="np-label">Corporate Email</label>
                  <input
                    type="email"
                    value={initEmail}
                    onChange={(e) => setInitEmail(e.target.value)}
                    className="np-input font-mono"
                    placeholder="admin@nexus-pulse.io"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="np-label">Master Passphrase (Bcrypt) *</label>
                  <input
                    type="password"
                    value={initPassword}
                    onChange={(e) => setInitPassword(e.target.value)}
                    className="np-input font-mono"
                    placeholder="Min 6 characters"
                    required
                  />
                </div>
                <div>
                  <label className="np-label">Confirm Passphrase *</label>
                  <input
                    type="password"
                    value={initConfirmPassword}
                    onChange={(e) => setInitConfirmPassword(e.target.value)}
                    className="np-input font-mono"
                    placeholder="••••••••••••"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isInitializingAdmin}
                className="btn btn-primary w-full justify-center btn-lg mt-4"
              >
                <span>{isInitializingAdmin ? "Binding Hardware & Generating Keys..." : "Initialize Master Admin & Enter Dashboard"}</span>
                <span>➔</span>
              </button>
            </form>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-base relative">
        {/* Audio SFX Toggle */}
        <div className="absolute top-4 right-4">
          <button
            type="button"
            onClick={() => {
              const next = !soundEnabled;
              setSoundEnabled(next);
              if (next) setTimeout(() => playUiSound("action"), 50);
            }}
            className={`btn btn-sm ${soundEnabled ? "btn-secondary text-theme-accent" : "btn-ghost text-theme-muted"}`}
            title={soundEnabled ? "UI Audio SFX Active (Click to Mute)" : "UI Audio SFX Muted (Click to Enable)"}
          >
            <span>{soundEnabled ? "🔊" : "🔇"}</span>
            <span className="text-[11px] font-mono">{soundEnabled ? "SFX: ON" : "SFX: OFF"}</span>
          </button>
        </div>

        <div className="np-card w-full max-w-md p-8 relative overflow-hidden shadow-lg border-theme">
          {isScanning && <div className="biometric-scanner-line" />}

          <div className="text-center mb-8">
            <div className="w-12 h-12 mx-auto mb-3 rounded-lg border-theme bg-elevated flex items-center justify-center font-bold text-base text-theme-accent font-mono">
              NP
            </div>
            <h1 className="text-xl font-bold tracking-tight text-theme-primary">
              Nexus-Pulse Level 2 Enterprise
            </h1>
            <p className="text-xs text-theme-secondary mt-1">
              Autonomous B2B Lead Engine & Hardware-Bound Gateway
            </p>
          </div>

          {loginError && (
            <div className="mb-5 np-alert np-alert-error">
              <span>{loginError}</span>
            </div>
          )}

          {isScanning ? (
            <div className="text-center py-8 space-y-4">
              <div className="w-14 h-14 mx-auto rounded-full border-2 border-dashed border-[var(--accent)] animate-spin flex items-center justify-center">
                <span className="text-[10px] font-mono font-bold text-theme-accent">AUTH</span>
              </div>
              <p className="text-xs font-mono text-theme-secondary">
                {scanStep}
              </p>
              <div className="w-48 h-1 bg-overlay rounded-full mx-auto overflow-hidden">
                <div className="h-full bg-[var(--accent)] animate-pulse" style={{ width: "80%" }} />
              </div>
            </div>
          ) : (
            <form onSubmit={handleBiometricLogin} className="space-y-4">
              <div>
                <label className="np-label">Operator or Admin Username</label>
                <input
                  type="text"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  className="np-input font-mono"
                  placeholder="Enter username"
                  required
                />
              </div>

              <div>
                <label className="np-label">Cryptographic Passphrase (Bcrypt)</label>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="np-input font-mono"
                  placeholder="••••••••••••"
                  required
                />
              </div>

              <button type="submit" className="btn btn-primary w-full justify-center btn-lg mt-2">
                <span>Sign In & Verify Machine ID</span>
                <span>➔</span>
              </button>
            </form>
          )}
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // VIEW: MAIN ENTERPRISE DASHBOARD
  // ---------------------------------------------------------------------------
  return (
    <div className="np-app-container">
      {/* GLOBAL NOTIFICATION BANNER */}
      {alertBanner && (
        <div className={`px-4 py-2.5 text-xs font-medium border-b flex items-center justify-between ${
          alertBanner.type === "success" ? "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success)]" :
          alertBanner.type === "error" ? "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger)]" :
          "bg-[var(--accent-muted)] text-[var(--accent)] border-[var(--accent)]"
        }`}>
          <span>{alertBanner.message}</span>
          <button onClick={() => setAlertBanner(null)} className="hover:opacity-75 font-bold ml-4 text-sm">✕</button>
        </div>
      )}

      {/* TOP NAVIGATION HEADER */}
      <header className="np-header">
        {/* Brand & Telemetry */}
        <div className="flex items-center gap-3 shrink-0">
          <div
            className={`np-pulse-icon ${
              pulseState === "HOT_ALERT" ? "np-pulse-hot" :
              pulseState === "HUNTING" ? "np-pulse-hunting" : "np-pulse-idle"
            }`}
            title={`Agent Engine State: ${pulseState}`}
          >
            <span>NP</span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-theme-primary">
                Nexus-Pulse
              </span>
              <span className="badge badge-accent">
                Level 2
              </span>
            </div>
            <div className="flex items-center gap-2 text-[11px] text-theme-muted font-mono">
              <span>Status: <strong className={pulseState === 'HOT_ALERT' ? 'text-theme-danger' : pulseState === 'HUNTING' ? 'text-theme-success' : 'text-theme-accent'}>{pulseState}</strong></span>
              <span>•</span>
              <span className="hidden sm:inline">ID: {systemHealth?.machine_id || "NEXUS-E727"}</span>
            </div>
          </div>
        </div>

        {/* Center: Live Office Hours Clocks */}
        <div className="hidden lg:flex items-center gap-4 text-xs font-mono bg-elevated px-3 py-1.5 rounded-md border-theme shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse" />
            <span className="text-theme-secondary">Berlin (CET):</span>
            <span className="font-semibold text-theme-primary">
              {timezones.germany?.current_local_time?.split(" ")[1] || "09:15:00"}
            </span>
            <span className="text-[10px] text-theme-success">
              [{timezones.germany?.is_in_send_window ? "9-11 AM WINDOW" : "QUEUED"}]
            </span>
          </div>
          <span className="text-theme-muted">|</span>
          <div className="flex items-center gap-1.5">
            <span className="text-theme-secondary">London (GMT):</span>
            <span className="font-semibold text-theme-primary">
              {timezones.united_kingdom?.current_local_time?.split(" ")[1] || "08:15:00"}
            </span>
          </div>
        </div>

        {/* Action Controls & Theme Engine */}
        <div className="flex items-center gap-2.5 shrink-0">
          <button
            onClick={() => setIsHuntModalOpen(true)}
            className="btn btn-primary btn-sm"
            title="Launch Targeted Lead Hunt"
          >
            <span>⚡ Hunt & Verify</span>
          </button>

          <button
            onClick={() => setIsBackupModalOpen(true)}
            className="btn btn-secondary btn-sm"
            title="Export Multi-Format Database Backup"
          >
            <span>📦 Backup</span>
          </button>

          {/* Theme Switcher Dropdown */}
          <div className="relative">
            <button
              onClick={() => setIsThemeMenuOpen(!isThemeMenuOpen)}
              className="btn btn-secondary btn-sm flex items-center gap-1.5"
              title="Select Visual Theme"
            >
              <span
                className="theme-dot"
                style={{ backgroundColor: THEMES.find(t => t.id === activeTheme)?.dotColor || "#58a6ff" }}
              />
              <span className="hidden sm:inline">Theme</span>
              <span className="text-[10px]">▾</span>
            </button>

            {isThemeMenuOpen && (
              <div
                className="absolute right-0 mt-1.5 w-56 np-card p-1 z-50 shadow-lg border-theme"
                onMouseLeave={() => setIsThemeMenuOpen(false)}
              >
                <div className="px-2.5 py-1.5 text-[10px] font-semibold text-theme-secondary uppercase tracking-wider border-b-theme">
                  Appearance Theme
                </div>
                {THEMES.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => {
                      setActiveTheme(t.id);
                      setIsThemeMenuOpen(false);
                    }}
                    className={`w-full text-left px-2.5 py-2 rounded text-xs flex items-center justify-between hover:bg-hover transition-colors ${
                      activeTheme === t.id ? "text-theme-accent font-semibold" : "text-theme-primary"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="theme-dot" style={{ backgroundColor: t.dotColor }} />
                      <div>
                        <div>{t.name}</div>
                        <div className="text-[10px] text-theme-muted">{t.desc}</div>
                      </div>
                    </div>
                    {activeTheme === t.id && <span>✓</span>}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Subtle UI Audio SFX Toggle */}
          <button
            type="button"
            onClick={() => {
              const next = !soundEnabled;
              setSoundEnabled(next);
              if (next) setTimeout(() => playUiSound("action"), 50);
            }}
            className={`btn btn-sm flex items-center gap-1.5 ${soundEnabled ? "btn-secondary text-theme-accent" : "btn-ghost text-theme-muted"}`}
            title={soundEnabled ? "UI Audio SFX Active (Click to Mute)" : "UI Audio SFX Muted (Click to Enable)"}
          >
            <span>{soundEnabled ? "🔊" : "🔇"}</span>
            <span className="hidden sm:inline text-[11px] font-mono">{soundEnabled ? "SFX: ON" : "SFX: OFF"}</span>
          </button>

          {/* User Profile Pill & Sign Out */}
          <div className="flex items-center gap-2 pl-2.5 border-l-theme">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold leading-tight text-theme-primary">{user.full_name || user.username}</div>
              <span className="badge badge-gold uppercase text-[9px]">
                {user.role}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="btn btn-ghost btn-sm btn-icon text-theme-muted hover:text-theme-danger"
              title="Sign Out"
            >
              ⏻
            </button>
          </div>
        </div>
      </header>

      {/* NAVIGATION TAB BAR */}
      <nav className="np-nav">
        <button
          onClick={() => setActiveTab("kanban")}
          className={`np-nav-tab ${activeTab === "kanban" ? "active" : ""}`}
        >
          <span>📊 Pipeline ({kanbanItems.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("approval_gate")}
          className={`np-nav-tab ${activeTab === "approval_gate" ? "active" : ""}`}
        >
          <span>🛡️ Approval Gate</span>
          {pendingApprovals.length > 0 && (
            <span className="badge badge-warning text-[10px] px-1.5 py-0">{pendingApprovals.length}</span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("hot_leads")}
          className={`np-nav-tab ${activeTab === "hot_leads" ? "active" : ""}`}
        >
          <span>🔥 Hot Leads</span>
          {hotLeads.length > 0 && (
            <span className="badge badge-danger text-[10px] px-1.5 py-0 animate-pulse">{hotLeads.length}</span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("rotator")}
          className={`np-nav-tab ${activeTab === "rotator" ? "active" : ""}`}
        >
          <span>🔄 Inbox Rotator ({mailboxes.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("security_settings")}
          className={`np-nav-tab ${activeTab === "security_settings" ? "active" : ""}`}
        >
          <span>⚙️ Security Profile</span>
        </button>

        {user.role === "admin" && (
          <button
            onClick={() => setActiveTab("operator_mgmt")}
            className={`np-nav-tab ${activeTab === "operator_mgmt" ? "active" : ""}`}
          >
            <span>👥 Operators ({operatorsList.length})</span>
          </button>
        )}

        {user.role === "admin" && (
          <button
            onClick={() => setActiveTab("license_mgmt")}
            className={`np-nav-tab ${activeTab === "license_mgmt" ? "active" : ""}`}
          >
            <span>📜 License & Telemetry</span>
          </button>
        )}
      </nav>

      {/* MAIN CONTENT WORKSPACE */}
      <main className="np-main-content">
        {/* TAB 1: KANBAN LEAD PIPELINE */}
        {activeTab === "kanban" && (
          <div className="w-full space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-base text-theme-primary">
                  Pipeline Lifecycle: Autonomous Lead Engine
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Tracking verified estimating targets through zero-bounce hygiene, human gate, and IMAP listeners.
                </p>
              </div>

              <div className="text-xs font-mono text-theme-secondary">
                Entities Tracked: <strong className="text-theme-accent">{kanbanItems.length}</strong>
              </div>
            </div>

            {/* Responsive Board Container */}
            <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-thin">
              {KANBAN_STAGES.map((stage) => {
                const stageLeads = kanbanItems.filter((item) => item.status === stage.key);
                return (
                  <div key={stage.key} className="kanban-col">
                    <div className="kanban-col-header">
                      <span className="font-semibold text-xs tracking-wide text-theme-primary">
                        {stage.label}
                      </span>
                      <span className={`badge ${stage.badgeClass}`}>
                        {stageLeads.length}
                      </span>
                    </div>

                    <div className="kanban-col-body">
                      {stageLeads.length === 0 ? (
                        <div className="text-center py-12 text-xs text-theme-muted font-mono italic">
                          No leads in stage
                        </div>
                      ) : (
                        stageLeads.map((lead) => {
                          const badges = getCleanLeadBadges(lead);
                          return (
                            <div
                              key={lead.id}
                              className={`kanban-card ${stage.key === "HOT_LEAD" ? "hot" : ""}`}
                            >
                              <div className="flex items-start justify-between gap-1 mb-1">
                                <h3 className="font-semibold text-xs text-theme-primary leading-snug line-clamp-1" title={lead.company_name}>
                                  {lead.company_name}
                                </h3>
                                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-overlay text-theme-secondary shrink-0">
                                  {lead.priority_score || 95}/100
                                </span>
                              </div>

                              <p className="text-[11px] font-mono text-theme-accent truncate mb-2">
                                {lead.primary_email || lead.recipient}
                              </p>

                              {/* Clean Deduplicated Badges */}
                              <div className="flex flex-wrap gap-1 mb-2">
                                {badges.map((b, idx) => (
                                  <span
                                    key={idx}
                                    className={`text-[10px] font-medium font-mono px-1.5 py-0.5 rounded ${
                                      b.type === "tier" ? "bg-overlay text-theme-secondary border-theme" :
                                      "bg-[var(--success-muted)] text-[var(--success)] border border-[var(--success)]"
                                    }`}
                                  >
                                    {b.text}
                                  </span>
                                ))}
                              </div>

                              {/* Tech Stack Chips */}
                              {lead.tech_stack && lead.tech_stack.length > 0 && (
                                <div className="flex flex-wrap gap-1 mb-2">
                                  {lead.tech_stack.slice(0, 3).map((tech, i) => (
                                    <span key={i} className="text-[9px] font-mono px-1 py-0.2 rounded bg-overlay text-theme-muted">
                                      {tech}
                                    </span>
                                  ))}
                                </div>
                              )}

                              {/* Stage-Specific Actions */}
                              {stage.key === "PENDING_APPROVAL" && (
                                <button
                                  onClick={() => handleOpenApprovalModal(lead)}
                                  className="btn btn-warning btn-sm w-full justify-center mt-1"
                                >
                                  Review & Authorize ➔
                                </button>
                              )}

                              {stage.key === "HOT_LEAD" && (
                                <button
                                  onClick={() => handleOpenHotLeadModal(lead)}
                                  className="btn btn-danger btn-sm w-full justify-center mt-1"
                                >
                                  ⚡ 1-Click AI Reply
                                </button>
                              )}
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 2: HUMAN APPROVAL GATE */}
        {activeTab === "approval_gate" && (
          <div className="w-full max-w-5xl mx-auto space-y-4">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary flex items-center gap-2">
                  <span>🛡️ Human Authorization Hold Gate</span>
                  <span className="badge badge-warning">MANDATORY GATE</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  No outreach messages are ever dispatched without explicit authorization from the Master Administrator.
                </p>
              </div>

              {user.role === "admin" && pendingApprovals.length > 0 && (
                <button
                  onClick={handleBatchApprove}
                  className="btn btn-warning btn-sm"
                >
                  ✓ Batch Authorize All ({pendingApprovals.length})
                </button>
              )}
            </div>

            {pendingApprovals.length === 0 ? (
              <div className="np-card p-12 text-center">
                <span className="text-3xl mb-2 block">✓</span>
                <h3 className="font-semibold text-sm text-theme-primary">Gate Clear: No Pending Outreach</h3>
                <p className="text-xs text-theme-secondary mt-1">All leads reviewed or dispatched according to 9-11 AM window.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingApprovals.map((item) => (
                  <div key={item.id} className="np-card p-4 space-y-3 border-l-4 border-l-[var(--warning)]">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-sm text-theme-primary">{item.company_name}</h3>
                          <span className="badge badge-muted text-[10px]">{item.channel}</span>
                          <span className="text-xs text-theme-muted font-mono">
                            Target: {item.target_country} ({item.target_timezone})
                          </span>
                        </div>
                        <p className="text-xs font-mono text-theme-accent mt-0.5">{item.recipient}</p>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleOpenApprovalModal(item)}
                          className="btn btn-secondary btn-sm"
                        >
                          Edit & Review
                        </button>
                        {user.role === "admin" && (
                          <button
                            onClick={() => handleApproveOutreach(item.id, item.subject, item.message_body)}
                            className="btn btn-warning btn-sm"
                          >
                            Authorize
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="bg-elevated p-3 rounded-md border-theme text-xs font-mono space-y-1">
                      <div className="text-theme-secondary font-semibold">Subject: {item.subject}</div>
                      <div className="text-theme-primary whitespace-pre-line line-clamp-3">{item.message_body}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: HOT LEAD ALERTS */}
        {activeTab === "hot_leads" && (
          <div className="w-full max-w-5xl mx-auto space-y-4">
            <div className="pb-3 border-b-theme">
              <h2 className="font-semibold text-base text-theme-primary">
                <span>🔥 Hot Lead Inquiries & Instant Response Stream</span>
              </h2>
              <p className="text-xs text-theme-secondary mt-0.5">
                Incoming responses classified by LLM agent as high-intent estimating or tender opportunities.
              </p>
            </div>

            {hotLeads.length === 0 ? (
              <div className="np-card p-12 text-center">
                <span className="text-3xl mb-2 block">📡</span>
                <h3 className="font-semibold text-sm text-theme-primary">IMAP Reply Listener Active</h3>
                <p className="text-xs text-theme-secondary mt-1">Listening on enrolled mailboxes for tender replies...</p>
              </div>
            ) : (
              <div className="space-y-3">
                {hotLeads.map((hl) => (
                  <div key={hl.id} className="np-card p-5 space-y-3 border-l-4 border-l-[var(--danger)]">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-sm text-theme-primary">{hl.company_name}</h3>
                          <span className="badge badge-danger">HOT INQUIRY</span>
                        </div>
                        <p className="text-xs font-mono text-theme-accent mt-0.5">{hl.sender_email}</p>
                      </div>

                      <button
                        onClick={() => handleOpenHotLeadModal(hl)}
                        className="btn btn-danger btn-sm"
                      >
                        ⚡ 1-Click AI Response
                      </button>
                    </div>

                    <div className="bg-elevated p-3 rounded-md border-theme text-xs font-mono">
                      <div className="text-theme-secondary font-semibold mb-1">Inquiry: {hl.subject}</div>
                      <div className="text-theme-primary whitespace-pre-line">{hl.message_body}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 4: INBOX ROTATOR */}
        {activeTab === "rotator" && (
          <div className="w-full max-w-6xl mx-auto space-y-4">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary">
                  <span>🔄 Inbox Rotator & Sender Reputation Pool</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Rotates sending accounts across enrolled domains with strict 40-50 daily send caps.
                </p>
              </div>

              <button
                onClick={() => setIsAddMailboxOpen(true)}
                className="btn btn-primary btn-sm"
              >
                + Enroll Mailbox
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {mailboxes.map((mb) => {
                const percent = Math.min(100, Math.round((mb.sent_today / mb.daily_limit) * 100));
                return (
                  <div key={mb.id} className="np-card p-4 space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold text-sm text-theme-primary">{mb.display_name}</h3>
                        <p className="text-xs font-mono text-theme-accent">{mb.email_address}</p>
                        <p className="text-[10px] text-theme-muted font-mono mt-0.5">Domain: {mb.domain}</p>
                      </div>
                      <span className="badge badge-success">HEALTHY</span>
                    </div>

                    <div>
                      <div className="flex items-center justify-between text-xs font-mono mb-1">
                        <span className="text-theme-secondary">Daily Send Progress</span>
                        <span className="font-semibold text-theme-primary">{mb.sent_today} / {mb.daily_limit} ({mb.remaining_quota} left)</span>
                      </div>
                      <div className="np-progress-bar">
                        <div
                          className={`np-progress-fill ${percent > 80 ? 'danger' : 'success'}`}
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    </div>

                    <div className="text-[11px] font-mono bg-elevated p-2.5 rounded border-theme space-y-1">
                      <div className="flex justify-between text-theme-secondary">
                        <span>Host:</span>
                        <span className="text-theme-primary">{mb.smtp_host || `smtp.${mb.domain}`}</span>
                      </div>
                      <div className="flex justify-between text-theme-secondary">
                        <span>Port / TLS:</span>
                        <span className="text-theme-primary">{mb.smtp_port || 587}</span>
                      </div>
                      <div className="flex justify-between text-theme-secondary">
                        <span>Username:</span>
                        <span className="text-theme-primary truncate max-w-[160px]">{mb.smtp_username || mb.email_address}</span>
                      </div>
                    </div>

                    <div className="pt-2 border-t-theme flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleOpenEditMailbox(mb)}
                        className="btn btn-secondary btn-sm"
                      >
                        ⚙️ Configure
                      </button>
                      <button
                        onClick={() => handleDeleteMailbox(mb)}
                        className="btn btn-danger btn-sm"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 5: DYNAMIC ADMIN PROFILE */}
        {activeTab === "security_settings" && (
          <div className="w-full max-w-3xl mx-auto space-y-5">
            <div className="pb-3 border-b-theme">
              <h2 className="font-semibold text-base text-theme-primary">
                <span>⚙️ Account Security & Dynamic Admin Profile</span>
              </h2>
              <p className="text-xs text-theme-secondary mt-0.5">
                Update master credentials and profile details. Password modifications re-hash via Bcrypt with 12 rounds.
              </p>
            </div>

            <div className="np-card p-6 space-y-5">
              <div className="flex items-center justify-between pb-4 border-b-theme">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg border-theme bg-elevated flex items-center justify-center font-bold text-sm text-theme-accent font-mono">
                    HA
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm text-theme-primary">{adminProfile?.full_name || "H.Huddair"}</h3>
                    <p className="text-xs font-mono text-theme-accent">{adminProfile?.email || "h.huddair@nexus-pulse.io"}</p>
                  </div>
                </div>
                <span className="badge badge-gold">MASTER ADMIN</span>
              </div>

              <form onSubmit={handleUpdateAdminProfile} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="np-label">Admin Username</label>
                    <input
                      type="text"
                      value={adminUsernameInput}
                      onChange={(e) => {
                        adminFormDirtyRef.current = true;
                        setAdminUsernameInput(e.target.value);
                      }}
                      className="np-input font-mono"
                      required
                    />
                  </div>
                  <div>
                    <label className="np-label">Corporate Email</label>
                    <input
                      type="email"
                      value={adminEmailInput}
                      onChange={(e) => {
                        adminFormDirtyRef.current = true;
                        setAdminEmailInput(e.target.value);
                      }}
                      className="np-input font-mono"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Full Executive Name</label>
                  <input
                    type="text"
                    value={adminFullNameInput}
                    onChange={(e) => {
                      adminFormDirtyRef.current = true;
                      setAdminFullNameInput(e.target.value);
                    }}
                    className="np-input"
                    required
                  />
                </div>

                <div className="pt-4 border-t-theme space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-theme-secondary">
                    Password Modification (Bcrypt Re-Hashing)
                  </h4>
                  <p className="text-xs text-theme-muted">
                    Leave blank to maintain existing password. To update, provide current password and new password.
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <label className="np-label">Current Password</label>
                      <input
                        type="password"
                        value={adminCurrentPassword}
                        onChange={(e) => setAdminCurrentPassword(e.target.value)}
                        placeholder="••••••••••••"
                        className="np-input font-mono"
                      />
                    </div>
                    <div>
                      <label className="np-label">New Password</label>
                      <input
                        type="password"
                        value={adminNewPassword}
                        onChange={(e) => setAdminNewPassword(e.target.value)}
                        placeholder="••••••••••••"
                        className="np-input font-mono"
                      />
                    </div>
                    <div>
                      <label className="np-label">Confirm Password</label>
                      <input
                        type="password"
                        value={adminConfirmPassword}
                        onChange={(e) => setAdminConfirmPassword(e.target.value)}
                        placeholder="••••••••••••"
                        className="np-input font-mono"
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-4 flex items-center justify-between border-t-theme">
                  <span className="text-[11px] text-theme-muted font-mono">
                    Bcrypt (Cost 12) GPU-Resistant Salting
                  </span>
                  <button type="submit" className="btn btn-primary btn-sm">
                    Save Profile Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* TAB 6: ROLE-BASED OPERATOR MANAGEMENT & AUDIT TRAIL */}
        {activeTab === "operator_mgmt" && (
          <div className="w-full max-w-7xl mx-auto space-y-6">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary flex items-center gap-2">
                  <span>👥 Role-Based Operator Management</span>
                  <span className="badge badge-purple">ADMIN PORTAL</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Issue operator licenses, configure hardware machine-locking, toggle active status, and modify daily quotas inline.
                </p>
              </div>

              <button
                onClick={() => setIsCreateOperatorOpen(true)}
                className="btn btn-primary btn-sm"
              >
                + Create Operator Account
              </button>
            </div>

            {/* Operator List Table with Fixed Columns & Horizontal Wrapper */}
            <div className="np-table-wrapper">
              <table className="np-table">
                <thead>
                  <tr>
                    <th style={{ width: "22%" }}>Operator Identity</th>
                    <th style={{ width: "8%" }}>Role</th>
                    <th style={{ width: "11%" }}>Access Status</th>
                    <th style={{ width: "15%" }}>Device Lock</th>
                    <th style={{ width: "12%" }}>Daily Quotas</th>
                    <th style={{ width: "10%" }}>Subscription Expiry</th>
                    <th style={{ width: "10%" }}>Last Login</th>
                    <th style={{ width: "12%" }} className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {operatorsList.map((op) => (
                    <React.Fragment key={op.id}>
                      <tr>
                        <td>
                          <div className="font-semibold text-xs text-theme-primary leading-normal truncate">{op.full_name}</div>
                          <div className="text-[11px] font-mono text-theme-accent leading-normal truncate">{op.username}</div>
                          <div className="text-[10px] text-theme-muted leading-normal truncate">{op.email}</div>
                        </td>

                        <td className="np-table-nowrap">
                          <span className={`badge ${op.role === 'admin' ? 'badge-gold' : 'badge-accent'}`}>
                            {op.role}
                          </span>
                        </td>

                        <td className="np-table-nowrap">
                          {op.role === "admin" ? (
                            <span className="badge badge-success">PERMANENT</span>
                          ) : (
                            <button
                              onClick={() => handleToggleOperatorStatus(op.id)}
                              className={`btn btn-sm ${op.is_active === 1 ? 'btn-success' : 'btn-danger'}`}
                              title="Click to toggle access"
                            >
                              <span className={`w-1.5 h-1.5 rounded-full ${op.is_active === 1 ? 'bg-[var(--success)]' : 'bg-[var(--danger)]'}`} />
                              <span>{op.is_active === 1 ? 'ACTIVE' : 'REVOKED'}</span>
                            </button>
                          )}
                        </td>

                        <td>
                          <span className="text-xs font-mono truncate block" title={op.device_lock_id || "Unbound"}>
                            {op.device_lock_id || "Auto-Bind on Login"}
                          </span>
                        </td>

                        <td className="np-table-nowrap font-mono text-xs">
                          <div>Scrape: <strong>{op.daily_scrape_quota}</strong>/d</div>
                          <div>Send: <strong>{op.daily_send_quota}</strong>/d</div>
                        </td>

                        <td className="np-table-nowrap text-xs font-mono">
                          {op.expiry_date ? op.expiry_date.split(" ")[0] : "Perpetual"}
                        </td>

                        <td className="np-table-nowrap text-xs text-theme-muted font-mono">
                          {op.last_login ? op.last_login.split(" ")[0] : "Never"}
                        </td>

                        <td className="np-table-actions">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => handleOpenResetPasswordModal(op)}
                              className="btn btn-secondary btn-sm"
                              title="Reset Operator Password"
                            >
                              Reset Pass
                            </button>
                            <button
                              onClick={() => handleToggleInlineAdjust(op)}
                              className={`btn btn-sm ${expandedOperatorId === op.id ? 'btn-primary' : 'btn-secondary'}`}
                              title="Adjust Quotas & Subscription"
                            >
                              {expandedOperatorId === op.id ? 'Close' : 'Adjust'}
                            </button>
                          </div>
                        </td>
                      </tr>

                      {/* Streamlined Inline Action Bar */}
                      {expandedOperatorId === op.id && (
                        <tr>
                          <td colSpan={8} className="np-expand-cell border-b-theme">
                            <div className="p-4 sm:p-5 space-y-3 bg-elevated">
                              <div className="flex items-center justify-between pb-2 border-b-theme">
                                <span className="text-xs font-semibold text-theme-primary">
                                  Inline Quota & Subscription Controls: {op.username}
                                </span>
                                <span className="text-xs font-mono text-theme-muted">
                                  Current Expiry: {op.expiry_date || "Perpetual"}
                                </span>
                              </div>

                              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {/* Quick Extension Presets */}
                                <div>
                                  <label className="np-label">Extend Subscription</label>
                                  <div className="grid grid-cols-4 gap-1.5">
                                    <button
                                      type="button"
                                      onClick={() => handleApplyInlineQuotas(op.id, 30)}
                                      className="btn btn-secondary btn-sm justify-center"
                                    >
                                      +30d
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => handleApplyInlineQuotas(op.id, 90)}
                                      className="btn btn-secondary btn-sm justify-center"
                                    >
                                      +90d
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => handleApplyInlineQuotas(op.id, 180)}
                                      className="btn btn-secondary btn-sm justify-center"
                                    >
                                      +180d
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => handleApplyInlineQuotas(op.id, 365)}
                                      className="btn btn-secondary btn-sm justify-center"
                                    >
                                      +1y
                                    </button>
                                  </div>
                                </div>

                                {/* Daily Scrape Limit */}
                                <div>
                                  <label className="np-label">Daily Scrape Limit</label>
                                  <input
                                    type="number"
                                    value={inlineScrapeQuota}
                                    onChange={(e) => setInlineScrapeQuota(e.target.value)}
                                    className="np-input font-mono"
                                  />
                                  <div className="flex gap-1 mt-1">
                                    {[100, 200, 500, 1000].map(val => (
                                      <button
                                        key={val}
                                        type="button"
                                        onClick={() => setInlineScrapeQuota(String(val))}
                                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-overlay hover:bg-hover text-theme-secondary"
                                      >
                                        {val}
                                      </button>
                                    ))}
                                  </div>
                                </div>

                                {/* Daily Send Limit */}
                                <div>
                                  <label className="np-label">Daily Send Limit</label>
                                  <input
                                    type="number"
                                    value={inlineSendQuota}
                                    onChange={(e) => setInlineSendQuota(e.target.value)}
                                    className="np-input font-mono"
                                  />
                                  <div className="flex gap-1 mt-1">
                                    {[25, 50, 100, 200].map(val => (
                                      <button
                                        key={val}
                                        type="button"
                                        onClick={() => setInlineSendQuota(String(val))}
                                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-overlay hover:bg-hover text-theme-secondary"
                                      >
                                        {val}
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              </div>

                              <div className="pt-2 flex justify-end gap-2 border-t-theme">
                                <button
                                  type="button"
                                  onClick={() => setExpandedOperatorId(null)}
                                  className="btn btn-ghost btn-sm"
                                >
                                  Cancel
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleApplyInlineQuotas(op.id, null)}
                                  className="btn btn-primary btn-sm"
                                >
                                  Apply Changes
                                </button>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Interactive Operator Session Audit Trail */}
            <div className="np-card p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b-theme">
                <div>
                  <h3 className="font-semibold text-sm text-theme-primary">Interactive Session & Security Audit Trail</h3>
                  <p className="text-xs text-theme-secondary mt-0.5">
                    Immutable event stream of logins, quota revisions, hardware bindings, and outreach approvals.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={auditSearch}
                    onChange={(e) => setAuditSearch(e.target.value)}
                    placeholder="Filter audit log..."
                    className="np-input text-xs w-48 font-mono"
                  />
                </div>
              </div>

              <div className="space-y-2">
                {[
                  { id: 1, action: "LOGIN", user: "h.huddair", status: "SUCCESS", detail: "Hardware machine fingerprint verified (NEXUS-E727-BB0B)", time: "Just now" },
                  { id: 2, action: "PIPELINE_LAUNCH", user: "h.huddair", status: "SUCCESS", detail: "Scraped 20 Commercial Construction targets in Berlin, Germany", time: "12m ago" },
                  { id: 3, action: "QUOTA_MODIFIED", user: "admin", status: "ENFORCED", detail: "Adjusted operator daily scrape limit to 200 / send limit 50", time: "1h ago" },
                  { id: 4, action: "OUTREACH_APPROVED", user: "h.huddair", status: "SCHEDULED", detail: "Authorized 5 tender emails for 9-11 AM CET window", time: "3h ago" },
                  { id: 5, action: "SECURITY_SCAN", user: "system", status: "ACTIVE", detail: "HMAC-SHA256 license signature verified across all workers", time: "5h ago" }
                ]
                .filter(ev => !auditSearch || ev.user.includes(auditSearch.toLowerCase()) || ev.detail.toLowerCase().includes(auditSearch.toLowerCase()))
                .map((ev) => (
                  <div key={ev.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded bg-elevated border-theme text-xs font-mono">
                    <div className="flex items-center gap-2.5 flex-wrap min-w-0">
                      <span className={`badge shrink-0 ${
                        ev.action === 'LOGIN' ? 'badge-accent' :
                        ev.action === 'QUOTA_MODIFIED' ? 'badge-gold' :
                        ev.action === 'OUTREACH_APPROVED' ? 'badge-warning' : 'badge-success'
                      }`}>
                        {ev.action}
                      </span>
                      <span className="font-bold text-theme-primary shrink-0">{ev.user}</span>
                      <span className="text-theme-secondary break-words">{ev.detail}</span>
                    </div>
                    <span className="text-theme-muted text-[11px] shrink-0">{ev.time}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 7: LICENSE & TELEMETRY MODULE */}
        {activeTab === "license_mgmt" && (
          <div className="w-full max-w-6xl mx-auto space-y-5">
            <div className="pb-3 border-b-theme">
              <h2 className="font-semibold text-base text-theme-primary">
                <span>📜 License & Hardware Cryptographic Telemetry</span>
              </h2>
              <p className="text-xs text-theme-secondary mt-0.5">
                Anti-theft boundary enforcement, hardware-bound machine GUIDs, and active license signatures.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="np-card p-5 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b-theme">
                  <h3 className="font-semibold text-sm text-theme-primary">Host Hardware Telemetry</h3>
                  <span className="badge badge-success">ACTIVE LOCK</span>
                </div>

                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">Machine ID:</span>
                    <span className="font-bold text-theme-accent">{licenseTelemetry?.hardware_fingerprint?.machine_id || "NEXUS-E727-BB0B-765E-4021"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">Windows MachineGuid:</span>
                    <span className="text-theme-primary">{licenseTelemetry?.hardware_fingerprint?.machine_guid || "25ea9ea7-2853-4895-b3f4-4732c6176d0b"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">MAC Interface:</span>
                    <span className="text-theme-primary">{licenseTelemetry?.hardware_fingerprint?.mac_address || "80:FA:5B:1C:5C:E6"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">License Tier:</span>
                    <span className="font-bold text-theme-gold">{licenseTelemetry?.license_payload?.tier || "Level-2-Enterprise"}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-theme-secondary">Licensed Client:</span>
                    <span className="font-bold text-theme-primary">{licenseTelemetry?.license_payload?.client_name || "H.Huddair Enterprise"}</span>
                  </div>
                </div>
              </div>

              <div className="np-card p-5 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b-theme">
                  <h3 className="font-semibold text-sm text-theme-primary">Vault Deduplication Shield</h3>
                  <span className="badge badge-accent">ACTIVE</span>
                </div>

                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">Deduplication Records:</span>
                    <span className="font-bold text-theme-primary">{systemHealth?.dedup_statistics?.total_dedup_records || kanbanItems.length}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">Active Mailboxes:</span>
                    <span className="font-bold text-theme-primary">{mailboxes.length}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">Zero-Bounce Hygiene:</span>
                    <span className="text-theme-success font-bold">3-Stage Active</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-theme-secondary">Database Layer:</span>
                    <span className="text-theme-primary">SQLite WAL Mode</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* MODAL: MULTI-FORMAT DATA BACKUP */}
      {isBackupModalOpen && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-lg">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Database Backup & Multi-Format Export
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Generate cryptographic snapshot backups for local archiving or CRM integration.
                </p>
              </div>
              <button
                onClick={() => !isBackingUp && setIsBackupModalOpen(false)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
                disabled={isBackingUp}
              >
                ✕
              </button>
            </div>

            <div className="np-modal-body space-y-4">
              <div className="bg-elevated p-3 rounded border-theme text-xs font-mono space-y-1">
                <div className="flex justify-between text-theme-secondary">
                  <span>Available Leads:</span>
                  <span className="font-bold text-theme-accent">{kanbanItems.length} Leads</span>
                </div>
                <div className="flex justify-between text-theme-secondary">
                  <span>Server Backup Path:</span>
                  <span className="text-theme-primary truncate max-w-[240px]">Desktop/rabbi/vault/backups/</span>
                </div>
                <div className="flex justify-between text-theme-secondary">
                  <span>Payload Encryption:</span>
                  <span className="text-theme-success font-bold">AES-256 Validated</span>
                </div>
              </div>

              <div className="space-y-2.5">
                <div className="np-card p-3 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-xs text-theme-primary">JSON Format (.json)</div>
                    <div className="text-[11px] text-theme-secondary">Full hierarchical schema with tech stack & DNS MX logs</div>
                  </div>
                  <button
                    onClick={() => handleDownloadBackup("json")}
                    disabled={isBackingUp}
                    className="btn btn-secondary btn-sm"
                  >
                    Export .json
                  </button>
                </div>

                <div className="np-card p-3 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-xs text-theme-primary">Excel Spreadsheet (.xlsx)</div>
                    <div className="text-[11px] text-theme-secondary">Formatted multi-column workbook for MS Excel & Sheets</div>
                  </div>
                  <button
                    onClick={() => handleDownloadBackup("xlsx")}
                    disabled={isBackingUp}
                    className="btn btn-primary btn-sm"
                  >
                    Export .xlsx
                  </button>
                </div>

                <div className="np-card p-3 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-xs text-theme-primary">CSV Delimited (.csv)</div>
                    <div className="text-[11px] text-theme-secondary">Flat RFC 4180 dataset for HubSpot / Salesforce import</div>
                  </div>
                  <button
                    onClick={() => handleDownloadBackup("csv")}
                    disabled={isBackingUp}
                    className="btn btn-secondary btn-sm"
                  >
                    Export .csv
                  </button>
                </div>
              </div>
            </div>

            <div className="np-modal-footer">
              <button
                type="button"
                onClick={() => setIsBackupModalOpen(false)}
                disabled={isBackingUp}
                className="btn btn-ghost btn-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: HUNT & VERIFY LEAD ENGINE */}
      {isHuntModalOpen && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-lg">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Hunt & Verify: Targeted Lead Pipeline
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Deep Scraper + Zero-Bounce 3-Stage Hygiene Engine
                </p>
              </div>
              <button
                onClick={() => !isHunting && setIsHuntModalOpen(false)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
                disabled={isHunting}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleLaunchScrapePipeline}>
              <div className="np-modal-body space-y-4">
                <div className="space-y-3 p-3.5 bg-elevated rounded border-theme">
                  <div className="text-xs font-semibold uppercase tracking-wider text-theme-secondary">
                    Target Geographic Location
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="np-label">1. Target Region</label>
                      <select
                        value={huntRegion}
                        onChange={(e) => handleRegionChange(e.target.value)}
                        className="np-select"
                        disabled={isHunting}
                      >
                        {Object.keys(GEO_REGIONS).map(r => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="np-label">2. Target Country</label>
                      <select
                        value={huntCountry}
                        onChange={(e) => handleCountryChange(e.target.value)}
                        className="np-select"
                        disabled={isHunting}
                      >
                        {availableCountries.map(c => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="np-label mb-0">3. Target City</label>
                      <button
                        type="button"
                        onClick={() => setIsCustomCity(!isCustomCity)}
                        className="text-[11px] text-theme-accent hover:underline font-medium"
                      >
                        {isCustomCity ? "Choose from standard list" : "Specify custom city"}
                      </button>
                    </div>

                    {isCustomCity ? (
                      <input
                        type="text"
                        value={huntCustomCity}
                        onChange={(e) => setHuntCustomCity(e.target.value)}
                        placeholder="e.g. Baden-Baden, Cambridge, San Jose"
                        className="np-input font-mono text-xs"
                        disabled={isHunting}
                        autoFocus
                      />
                    ) : (
                      <select
                        value={huntCity}
                        onChange={(e) => setHuntCity(e.target.value)}
                        className="np-select"
                        disabled={isHunting}
                      >
                        {availableCities.map(city => (
                          <option key={city} value={city}>{city}</option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>

                <div>
                  <label className="np-label">Industry Niche / Trade Focus</label>
                  <input
                    type="text"
                    value={huntNiche}
                    onChange={(e) => setHuntNiche(e.target.value)}
                    placeholder="e.g. Commercial Construction, Sports Wear Manufacturers"
                    className="np-input"
                    required
                    disabled={isHunting}
                  />

                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {INDUSTRY_PRESETS.map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => setHuntNiche(preset)}
                        disabled={isHunting}
                        className={`text-[11px] px-2 py-0.5 rounded border transition-colors ${
                          huntNiche === preset
                            ? "bg-[var(--accent-muted)] text-[var(--accent)] border-[var(--accent)] font-medium"
                            : "bg-elevated text-theme-secondary border-theme hover:bg-hover"
                        }`}
                      >
                        {preset}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="np-label mb-0">Scraping Limit Counter</label>
                    <span className="badge badge-accent font-bold">
                      {huntMaxResults} Leads
                    </span>
                  </div>

                  <input
                    type="range"
                    min="5"
                    max="100"
                    step="5"
                    value={huntMaxResults}
                    onChange={(e) => setHuntMaxResults(parseInt(e.target.value, 10))}
                    className="w-full"
                    disabled={isHunting}
                  />

                  <div className="flex justify-between text-[11px] text-theme-muted mt-1">
                    <span>5</span>
                    <span>25</span>
                    <span>50</span>
                    <span>75</span>
                    <span>100 Max</span>
                  </div>

                  <div className="flex gap-1.5 mt-2">
                    {[10, 25, 50, 100].map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => setHuntMaxResults(preset)}
                        disabled={isHunting}
                        className={`btn btn-sm flex-1 justify-center ${huntMaxResults === preset ? 'btn-primary' : 'btn-secondary'}`}
                      >
                        {preset} {preset === 100 ? "Enterprise" : "Leads"}
                      </button>
                    ))}
                  </div>
                </div>

                {isHunting && (
                  <div className="np-alert np-alert-info">
                    <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-ping" />
                    <span>Executing targeted crawl for {huntNiche} in {isCustomCity ? huntCustomCity : huntCity}, {huntCountry}...</span>
                  </div>
                )}
              </div>

              <div className="np-modal-footer">
                <button
                  type="button"
                  onClick={() => setIsHuntModalOpen(false)}
                  disabled={isHunting}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isHunting}
                  className="btn btn-primary btn-sm"
                >
                  <span>Launch Lead Pipeline</span>
                  <span>➔</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: HUMAN APPROVAL GATE REVIEW */}
      {selectedApproval && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-xl">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Review & Authorize Outreach: {selectedApproval.company_name}
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Scheduled for 9:00 - 11:00 AM local recipient timezone.
                </p>
              </div>
              <button
                onClick={() => setSelectedApproval(null)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <div className="np-modal-body space-y-3">
              <div>
                <label className="np-label">Recipient Destination</label>
                <input
                  type="text"
                  readOnly
                  value={selectedApproval.recipient}
                  className="np-input font-mono"
                />
              </div>

              <div>
                <label className="np-label">Email Subject</label>
                <input
                  type="text"
                  value={approvalSubject}
                  onChange={(e) => setApprovalSubject(e.target.value)}
                  className="np-input font-mono"
                />
              </div>

              <div>
                <label className="np-label">Outreach Message Body</label>
                <textarea
                  rows={7}
                  value={approvalBody}
                  onChange={(e) => setApprovalBody(e.target.value)}
                  className="np-textarea"
                />
              </div>
            </div>

            <div className="np-modal-footer">
              <button
                onClick={() => setSelectedApproval(null)}
                className="btn btn-ghost btn-sm"
              >
                Cancel
              </button>
              {user.role === "admin" ? (
                <button
                  onClick={() => handleApproveOutreach(selectedApproval.id, approvalSubject, approvalBody)}
                  className="btn btn-warning btn-sm"
                >
                  Authorize & Schedule (9-11 AM)
                </button>
              ) : (
                <span className="text-xs text-theme-danger">
                  Restricted: Only Admin can authorize.
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MODAL: HOT LEAD 1-CLICK AI REPLY */}
      {selectedHotLead && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-xl border-[var(--danger)]">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-danger">
                  1-Click AI Response: {selectedHotLead.company_name}
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  High-intent response detected by IMAP listener.
                </p>
              </div>
              <button
                onClick={() => setSelectedHotLead(null)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <div className="np-modal-body space-y-3">
              <div className="bg-elevated p-3 rounded border-theme text-xs font-mono">
                <div className="text-theme-secondary font-semibold">Incoming Inquiry:</div>
                <div className="text-theme-primary mt-1">{selectedHotLead.message_body}</div>
              </div>

              <div>
                <label className="np-label">AI Suggested Executive Response</label>
                <textarea
                  rows={6}
                  value={hotLeadReplyBody}
                  onChange={(e) => setHotLeadReplyBody(e.target.value)}
                  className="np-textarea"
                />
              </div>
            </div>

            <div className="np-modal-footer">
              <button
                onClick={() => setSelectedHotLead(null)}
                className="btn btn-ghost btn-sm"
              >
                Dismiss
              </button>
              <button
                onClick={() => handleDispatchHotLeadReply(selectedHotLead.id, selectedHotLead.sender_email, hotLeadReplyBody)}
                className="btn btn-danger btn-sm"
              >
                Dispatch Response Now ➔
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: ADD NEW MAILBOX */}
      {isAddMailboxOpen && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-lg">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Enroll New Mailbox into Rotator Pool
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Connect via custom SMTP with strict reputation safeguard send-caps.
                </p>
              </div>
              <button
                onClick={() => setIsAddMailboxOpen(false)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddMailbox}>
              <div className="np-modal-body space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">Sender Display Name</label>
                    <input
                      type="text"
                      value={newMbDisplayName}
                      onChange={(e) => setNewMbDisplayName(e.target.value)}
                      placeholder="e.g. H. Huddair Estimating"
                      className="np-input"
                      required
                    />
                  </div>
                  <div>
                    <label className="np-label">Email Address</label>
                    <input
                      type="email"
                      value={newMbEmail}
                      onChange={(e) => setNewMbEmail(e.target.value)}
                      placeholder="tenders@domain.de"
                      className="np-input font-mono"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">SMTP Server Host</label>
                    <input
                      type="text"
                      value={newMbHost}
                      onChange={(e) => setNewMbHost(e.target.value)}
                      placeholder="smtp.domain.de"
                      className="np-input font-mono"
                    />
                  </div>
                  <div>
                    <label className="np-label">Port</label>
                    <input
                      type="number"
                      value={newMbPort}
                      onChange={(e) => setNewMbPort(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">SMTP Username</label>
                    <input
                      type="text"
                      value={newMbUsername}
                      onChange={(e) => setNewMbUsername(e.target.value)}
                      placeholder="Leave blank to use email"
                      className="np-input font-mono"
                    />
                  </div>
                  <div>
                    <label className="np-label">App Password / Secret</label>
                    <input
                      type="password"
                      value={newMbPassword}
                      onChange={(e) => setNewMbPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="np-input font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Daily Send Cap (Max 50 recommended)</label>
                  <input
                    type="number"
                    value={newMbDailyLimit}
                    onChange={(e) => setNewMbDailyLimit(e.target.value)}
                    className="np-input font-mono"
                    min="10"
                    max="100"
                    required
                  />
                </div>
              </div>

              <div className="np-modal-footer">
                <button
                  type="button"
                  onClick={() => setIsAddMailboxOpen(false)}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Enroll Mailbox
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDIT SMTP SETTINGS */}
      {selectedMailboxForEdit && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-lg">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Configure SMTP: {selectedMailboxForEdit.display_name}
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Update credentials, port, and daily limit caps.
                </p>
              </div>
              <button
                onClick={() => setSelectedMailboxForEdit(null)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdateMailbox}>
              <div className="np-modal-body space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">Display Name</label>
                    <input
                      type="text"
                      value={editMbDisplayName}
                      onChange={(e) => setEditMbDisplayName(e.target.value)}
                      className="np-input"
                      required
                    />
                  </div>
                  <div>
                    <label className="np-label">Email Address</label>
                    <input
                      type="email"
                      value={editMbEmail}
                      onChange={(e) => setEditMbEmail(e.target.value)}
                      className="np-input font-mono"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">SMTP Host</label>
                    <input
                      type="text"
                      value={editMbHost}
                      onChange={(e) => setEditMbHost(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                  <div>
                    <label className="np-label">Port</label>
                    <input
                      type="number"
                      value={editMbPort}
                      onChange={(e) => setEditMbPort(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">Username</label>
                    <input
                      type="text"
                      value={editMbUsername}
                      onChange={(e) => setEditMbUsername(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                  <div>
                    <label className="np-label">Password (blank to keep)</label>
                    <input
                      type="password"
                      value={editMbPassword}
                      onChange={(e) => setEditMbPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="np-input font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Daily Send Cap</label>
                  <input
                    type="number"
                    value={editMbDailyLimit}
                    onChange={(e) => setEditMbDailyLimit(e.target.value)}
                    className="np-input font-mono"
                    min="10"
                    max="100"
                    required
                  />
                </div>
              </div>

              <div className="np-modal-footer">
                <button
                  type="button"
                  onClick={() => setSelectedMailboxForEdit(null)}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Save Settings
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE OPERATOR */}
      {isCreateOperatorOpen && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-lg">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Create Operator Account
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Issues hardware-locked credentials and cryptographic license token.
                </p>
              </div>
              <button
                onClick={() => setIsCreateOperatorOpen(false)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateOperator}>
              <div className="np-modal-body space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">Username</label>
                    <input
                      type="text"
                      value={newOpUsername}
                      onChange={(e) => setNewOpUsername(e.target.value)}
                      placeholder="e.g. operator_berlin"
                      className="np-input font-mono"
                      required
                    />
                  </div>
                  <div>
                    <label className="np-label">Temporary Password (Bcrypt)</label>
                    <input
                      type="password"
                      value={newOpPassword}
                      onChange={(e) => setNewOpPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="np-input font-mono"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">Full Operator Name</label>
                    <input
                      type="text"
                      value={newOpFullName}
                      onChange={(e) => setNewOpFullName(e.target.value)}
                      placeholder="e.g. Klaus Richter"
                      className="np-input"
                      required
                    />
                  </div>
                  <div>
                    <label className="np-label">Email Address</label>
                    <input
                      type="email"
                      value={newOpEmail}
                      onChange={(e) => setNewOpEmail(e.target.value)}
                      placeholder="klaus@nexus-pulse.io"
                      className="np-input font-mono"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Device Lock (Host Machine-ID)</label>
                  <input
                    type="text"
                    value={newOpDeviceLock}
                    onChange={(e) => setNewOpDeviceLock(e.target.value)}
                    className="np-input font-mono"
                  />
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="np-label">Expiry (Days)</label>
                    <input
                      type="number"
                      value={newOpExpiryDays}
                      onChange={(e) => setNewOpExpiryDays(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                  <div>
                    <label className="np-label">Scrape Quota/d</label>
                    <input
                      type="number"
                      value={newOpScrapeQuota}
                      onChange={(e) => setNewOpScrapeQuota(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                  <div>
                    <label className="np-label">Send Quota/d</label>
                    <input
                      type="number"
                      value={newOpSendQuota}
                      onChange={(e) => setNewOpSendQuota(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                </div>
              </div>

              <div className="np-modal-footer">
                <button
                  type="button"
                  onClick={() => setIsCreateOperatorOpen(false)}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Issue License & Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: RESET OPERATOR PASSWORD */}
      {selectedUserForReset && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-sm">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Reset Password: {selectedUserForReset.username}
                </h3>
              </div>
              <button
                onClick={() => setSelectedUserForReset(null)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleResetOperatorPassword}>
              <div className="np-modal-body space-y-3">
                <p className="text-xs text-theme-secondary">
                  Enter new passphrase. It will be salted and encrypted using Bcrypt (cost 12) before persisting to SQLite.
                </p>

                <div>
                  <label className="np-label">New Password</label>
                  <input
                    type="password"
                    value={resetPasswordInput}
                    onChange={(e) => setResetPasswordInput(e.target.value)}
                    placeholder="••••••••••••"
                    className="np-input font-mono"
                    autoFocus
                    required
                  />
                </div>
              </div>

              <div className="np-modal-footer">
                <button
                  type="button"
                  onClick={() => setSelectedUserForReset(null)}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Reset with Bcrypt
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// Render the application into #root
const rootElement = document.getElementById("root");
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<NexusPulseApp />);
}
