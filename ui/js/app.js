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
  const [pulseState, setPulseState] = useState("RUNNING"); // 'RUNNING', 'DISPATCHING', 'HUNTING', 'HOT_ALERT', 'IDLE'
  const [dispatcherState, setDispatcherState] = useState({ status: "RUNNING", bypass_window: false });
  const [isDispatchingNow, setIsDispatchingNow] = useState(false);
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
  const [newOpDeviceLock, setNewOpDeviceLock] = useState("");
  const [newOpExpiryDays, setNewOpExpiryDays] = useState("90");
  const [newOpScrapeQuota, setNewOpScrapeQuota] = useState("200");
  const [newOpSendQuota, setNewOpSendQuota] = useState("50");
  const [isCreatingOperator, setIsCreatingOperator] = useState(false);
  const [isResettingPassword, setIsResettingPassword] = useState(false);
  const [updatingOperatorId, setUpdatingOperatorId] = useState(null);
  const [sessionAuditLogs, setSessionAuditLogs] = useState([]);

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
  // SAAS EXPANSION STATE: TEMPLATES, BILLING, BLACKLIST & ANALYTICS
  // ---------------------------------------------------------------------------
  const [huntTargetUrls, setHuntTargetUrls] = useState("");

  const [templatesList, setTemplatesList] = useState([]);
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [tplTitle, setTplTitle] = useState("");
  const [tplNiche, setTplNiche] = useState("Commercial Construction");
  const [tplSubject, setTplSubject] = useState("");
  const [tplBody, setTplBody] = useState("");
  const [tplIsDefault, setTplIsDefault] = useState(false);

  const [deliverabilityStats, setDeliverabilityStats] = useState({
    total_sent: 0,
    total_delivered: 0,
    total_opened: 0,
    total_bounced: 0,
    total_replied: 0,
    total_hot_leads: 0,
    total_queued: 0,
    total_suppressed: 0,
    open_rate_percent: 0.0,
    bounce_rate_percent: 0.0,
    conversion_rate_percent: 0.0
  });
  const [isPollingImap, setIsPollingImap] = useState(false);

  const [blacklistRules, setBlacklistRules] = useState([]);
  const [newRulePattern, setNewRulePattern] = useState("");
  const [newRuleReason, setNewRuleReason] = useState("");

  const [billingHistory, setBillingHistory] = useState([]);
  const [billingTargetOpId, setBillingTargetOpId] = useState("");
  const [billingBasePrice, setBillingBasePrice] = useState("199.00");
  const [billingDurationDays, setBillingDurationDays] = useState(90);
  const [billingNotes, setBillingNotes] = useState("");
  const [isApplyingBilling, setIsApplyingBilling] = useState(false);

  // ---------------------------------------------------------------------------
  // FETCH CORE DATA (4-Second Periodic Polling)
  // ---------------------------------------------------------------------------
  const fetchData = async () => {
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const [healthRes, kanbanRes, approvalsRes, hotLeadsRes, mailboxesRes, tzRes, dispRes] = await Promise.all([
        fetch(`${API_BASE}/api/health`, { headers }).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/kanban/leads`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/outreach/pending`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/outreach/hot-leads`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/outreach/mailboxes`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/scheduler/timezones`, { headers }).then(r => r.json()).catch(() => ({})),
        fetch(`${API_BASE}/api/dispatcher/status`, { headers }).then(r => r.json()).catch(() => null)
      ]);

      if (healthRes) setSystemHealth(healthRes);
      if (Array.isArray(kanbanRes)) setKanbanItems(kanbanRes);
      if (Array.isArray(approvalsRes)) setPendingApprovals(approvalsRes);
      if (dispRes) setDispatcherState(dispRes);

      if (Array.isArray(hotLeadsRes)) {
        setHotLeads(hotLeadsRes);
        if (hotLeadsRes.length > 0) {
          setPulseState("HOT_ALERT");
        } else if (isDispatchingNow || (dispRes && dispRes.status === "DISPATCHING")) {
          setPulseState("DISPATCHING");
        } else if (dispRes && dispRes.status === "RUNNING") {
          setPulseState("RUNNING");
        } else if (approvalsRes && approvalsRes.length > 0) {
          setPulseState("RUNNING");
        } else {
          setPulseState("RUNNING");
        }
      } else if (dispRes && dispRes.status) {
        setPulseState(dispRes.status === "DISPATCHING" ? "DISPATCHING" : "RUNNING");
      }
      if (Array.isArray(mailboxesRes)) setMailboxes(mailboxesRes);
      if (tzRes) setTimezones(tzRes);

      // Fetch templates & deliverability analytics for all roles
      fetch(`${API_BASE}/api/templates`, { headers }).then(r => r.json()).then(data => {
        if (Array.isArray(data)) setTemplatesList(data);
      }).catch(() => {});

      fetch(`${API_BASE}/api/analytics/deliverability`, { headers }).then(r => r.json()).then(data => {
        if (data && typeof data.total_sent === "number") setDeliverabilityStats(data);
      }).catch(() => {});

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

        fetch(`${API_BASE}/api/blacklist`, { headers }).then(r => r.json()).then(data => {
          if (Array.isArray(data)) setBlacklistRules(data);
        }).catch(() => {});

        fetch(`${API_BASE}/api/billing/all-history`, { headers }).then(r => r.json()).then(data => {
          if (Array.isArray(data)) setBillingHistory(data);
        }).catch(() => {});

        fetch(`${API_BASE}/api/operators/activity-log/all`, { headers }).then(r => r.json()).then(data => {
          if (Array.isArray(data)) setSessionAuditLogs(data);
        }).catch(() => {});
      }
    } catch (e) {
      console.error("Data sync error:", e);
    }
  };

  // Restrict Operator access away from Admin tabs
  useEffect(() => {
    if (user && user.role === "operator") {
      const adminOnlyTabs = ["security_settings", "operator_mgmt", "license_mgmt", "billing_mgmt", "blacklist_mgmt"];
      if (adminOnlyTabs.includes(activeTab)) {
        setActiveTab("kanban");
      }
    }
  }, [user, activeTab]);

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
          max_results: parseInt(huntMaxResults, 10) || 20,
          target_urls: huntTargetUrls.trim() ? huntTargetUrls.split("\n").map(u => u.trim()).filter(Boolean) : undefined
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
          message: `Outreach item approved by ${user.username}! Timezone-aware dispatch active (9:00 AM - 5:00 PM local window).`
        });
        fetchData();
      } else {
        alert(data.detail || "Approval failed.");
      }
    } catch (e) {
      alert("Error approving outreach.");
    }
  };

  const handleDispatchQueueNow = async (bypassWindow = true, specificQueueId = null) => {
    setIsDispatchingNow(true);
    setPulseState("DISPATCHING");
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/dispatch-now`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          bypass_window: bypassWindow,
          queue_id: specificQueueId
        })
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setAlertBanner({
          type: "success",
          message: `⚡ Dispatch Engine Triggered: ${data.dispatched_count || 0} leads dispatched! (${data.scheduled_count || 0} queued for local business hours)`
        });
        fetchData();
      } else {
        setAlertBanner({
          type: "danger",
          message: data.detail || data.message || "Dispatch queue trigger failed."
        });
      }
    } catch (err) {
      setAlertBanner({
        type: "danger",
        message: "Error executing dispatch trigger."
      });
    } finally {
      setIsDispatchingNow(false);
    }
  };

  const handleToggleDispatcherBypass = async (enabled) => {
    try {
      const resp = await fetch(`${API_BASE}/api/dispatcher/toggle-bypass`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ bypass_window: enabled })
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setDispatcherState(prev => ({ ...prev, bypass_window: enabled }));
        setAlertBanner({
          type: "info",
          message: enabled
            ? "⚡ Dispatcher Bypass Window ENABLED: 24/7 immediate dispatch active for testing/weekends."
            : "🕒 Dispatcher Window RESTORED: Standard 9:00 AM - 5:00 PM local recipient business hours active."
        });
        fetchData();
      }
    } catch (err) {
      setAlertBanner({ type: "danger", message: "Failed to toggle dispatcher bypass window." });
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
    // Instant optimistic update for smooth UI response
    setOperatorsList(prev => prev.map(op => {
      if (op.id === operatorId) {
        return { ...op, is_active: op.is_active === 1 ? 0 : 1 };
      }
      return op;
    }));
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
        fetchData();
        setAlertBanner({ type: "danger", message: data.detail || "Status toggle failed." });
      }
    } catch (err) {
      fetchData();
      setAlertBanner({ type: "danger", message: "Error toggling operator status." });
    }
  };

  const handleOpenResetPasswordModal = (op) => {
    setSelectedUserForReset(op);
    setResetPasswordInput("");
  };

  const handleResetOperatorPassword = async (e) => {
    if (e) e.preventDefault();
    if (!resetPasswordInput || resetPasswordInput.length < 6) {
      setAlertBanner({ type: "warning", message: "Passphrase must be at least 6 characters." });
      return;
    }
    setIsResettingPassword(true);
    try {
      const resp = await fetch(`${API_BASE}/api/operators/${selectedUserForReset.id}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ new_password: resetPasswordInput })
      });
      const data = await resp.json();
      if (resp.ok) {
        setSelectedUserForReset(null);
        setResetPasswordInput("");
        setAlertBanner({ type: "success", message: `Password reset successfully for ${data.username} using Bcrypt encryption.` });
        fetchData();
      } else {
        setAlertBanner({ type: "danger", message: data.detail || "Password reset failed." });
      }
    } catch (err) {
      setAlertBanner({ type: "danger", message: "Error resetting password." });
    } finally {
      setIsResettingPassword(false);
    }
  };

  const handleDeleteOperator = async (op) => {
    if (!op || op.role === "admin") {
      setAlertBanner({ type: "danger", message: "Master Administrator accounts cannot be deleted." });
      return;
    }

    const confirmed = window.confirm(
      `⚠️ PERMANENT OPERATOR REMOVAL\n\nAre you sure you want to permanently delete operator "${op.username}" (${op.full_name || "Operator"})?\n\nThis will remove their account and revoke license access. All existing leads and pipeline data will remain preserved.`
    );
    if (!confirmed) return;

    try {
      const resp = await fetch(`${API_BASE}/api/operators/${op.id}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        }
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setOperatorsList(prev => prev.filter(item => item.id !== op.id));
        if (expandedOperatorId === op.id) {
          setExpandedOperatorId(null);
        }
        setAlertBanner({
          type: "success",
          message: `Operator "${op.username}" was permanently removed.`
        });
        fetchData();
      } else {
        setAlertBanner({
          type: "danger",
          message: data.detail || data.message || "Failed to delete operator account."
        });
      }
    } catch (err) {
      setAlertBanner({
        type: "danger",
        message: "Network error occurred while deleting operator."
      });
    }
  };

  const handleCreateOperator = async (e) => {
    if (e) e.preventDefault();
    if (!newOpUsername || newOpUsername.trim().length < 3) {
      setAlertBanner({ type: "warning", message: "Username must be at least 3 characters." });
      return;
    }
    if (!newOpPassword || newOpPassword.length < 6) {
      setAlertBanner({ type: "warning", message: "Passphrase must be at least 6 characters." });
      return;
    }
    setIsCreatingOperator(true);
    try {
      const resp = await fetch(`${API_BASE}/api/operators`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          username: newOpUsername.trim(),
          password: newOpPassword,
          full_name: newOpFullName.trim() || newOpUsername.trim(),
          email: newOpEmail.trim(),
          device_lock_id: newOpDeviceLock.trim() || undefined,
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
        setNewOpDeviceLock("");
        setNewOpExpiryDays("90");
        setNewOpScrapeQuota("200");
        setNewOpSendQuota("50");
        setAlertBanner({ type: "success", message: `Operator account '${data.username}' created with signed license token!` });
        fetchData();
      } else {
        setAlertBanner({ type: "danger", message: data.detail || "Operator creation failed." });
      }
    } catch (err) {
      setAlertBanner({ type: "danger", message: "Error creating operator." });
    } finally {
      setIsCreatingOperator(false);
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
    setUpdatingOperatorId(operatorId);
    // Instant optimistic update
    setOperatorsList(prev => prev.map(op => {
      if (op.id === operatorId) {
        return {
          ...op,
          daily_scrape_quota: parseInt(inlineScrapeQuota, 10) || op.daily_scrape_quota,
          daily_send_quota: parseInt(inlineSendQuota, 10) || op.daily_send_quota
        };
      }
      return op;
    }));
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
        fetchData();
        setAlertBanner({ type: "danger", message: data.detail || "Quota modification failed." });
      }
    } catch (err) {
      fetchData();
      setAlertBanner({ type: "danger", message: "Error modifying quotas." });
    } finally {
      setUpdatingOperatorId(null);
    }
  };

  // ---------------------------------------------------------------------------
  // TEMPLATE MANAGEMENT HANDLERS
  // ---------------------------------------------------------------------------
  const handleOpenTemplateModal = (tpl = null) => {
    if (tpl) {
      setEditingTemplate(tpl);
      setTplTitle(tpl.title || "");
      setTplNiche(tpl.niche || "Commercial Construction");
      setTplSubject(tpl.subject_template || "");
      setTplBody(tpl.body_template || "");
      setTplIsDefault(Boolean(tpl.is_default));
    } else {
      setEditingTemplate(null);
      setTplTitle("");
      setTplNiche("Commercial Construction");
      setTplSubject("Commercial Estimation & Tenders // {{company_name}}");
      setTplBody(
        "Dear Estimating Team at {{company_name}},\n\n" +
        "We are reaching out regarding commercial capacity and tender packages for {{niche}} in {{country}}.\n\n" +
        "Our team handles detailed bill-of-quantities takeoffs, rapid estimating, and competitive pricing.\n\n" +
        "Please confirm the right contact or portal to receive tender specifications.\n\n" +
        "Best regards,\n" +
        "Commercial Estimating Team\n\n" +
        "---\n" +
        "To opt-out from future notices: {{unsubscribe_link}}"
      );
      setTplIsDefault(false);
    }
    setIsTemplateModalOpen(true);
  };

  const handleSaveTemplate = async (e) => {
    if (e) e.preventDefault();
    if (!tplTitle.trim() || !tplSubject.trim() || !tplBody.trim()) {
      alert("Please provide title, subject, and body for the template.");
      return;
    }
    try {
      const headers = {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      };
      if (editingTemplate) {
        const resp = await fetch(`${API_BASE}/api/templates/${editingTemplate.id}`, {
          method: "PUT",
          headers,
          body: JSON.stringify({
            title: tplTitle,
            niche: tplNiche,
            subject_template: tplSubject,
            body_template: tplBody,
            is_default: tplIsDefault
          })
        });
        if (resp.ok) {
          setAlertBanner({ type: "success", message: `Template '${tplTitle}' updated successfully.` });
          setIsTemplateModalOpen(false);
          fetchData();
        } else {
          const err = await resp.json();
          alert(err.detail || "Failed to update template.");
        }
      } else {
        const resp = await fetch(`${API_BASE}/api/templates`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            title: tplTitle,
            niche: tplNiche,
            subject_template: tplSubject,
            body_template: tplBody,
            is_default: tplIsDefault
          })
        });
        if (resp.ok) {
          setAlertBanner({ type: "success", message: `Template '${tplTitle}' created successfully.` });
          setIsTemplateModalOpen(false);
          fetchData();
        } else {
          const err = await resp.json();
          alert(err.detail || "Failed to create template.");
        }
      }
    } catch (e) {
      console.error(e);
      alert("Template save error.");
    }
  };

  const handleDeleteTemplate = async (tplId) => {
    if (!confirm("Are you sure you want to delete this proposal template?")) return;
    try {
      const resp = await fetch(`${API_BASE}/api/templates/${tplId}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (resp.ok) {
        setAlertBanner({ type: "info", message: "Template removed." });
        fetchData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleInsertTag = (tag) => {
    setTplBody(prev => prev + " " + tag);
  };

  // ---------------------------------------------------------------------------
  // MANUAL BILLING CONTROLS HANDLERS
  // ---------------------------------------------------------------------------
  const handleApplyBilling = async (e) => {
    if (e) e.preventDefault();
    if (!billingTargetOpId) {
      alert("Please select a target operator.");
      return;
    }
    const price = parseFloat(billingBasePrice) || 0;
    if (price <= 0) {
      alert("Please enter a valid Base Price.");
      return;
    }
    setIsApplyingBilling(true);
    try {
      const resp = await fetch(`${API_BASE}/api/operators/${billingTargetOpId}/billing`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          base_price: price,
          duration_days: billingDurationDays,
          notes: billingNotes.trim() || undefined
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({
          type: "success",
          message: `Billing applied! +${data.duration_days}d extension for $${data.final_price} (Expiry: ${data.new_expiry_date}).`
        });
        fetchData();
        setBillingNotes("");
      } else {
        alert(data.detail || "Billing application failed.");
      }
    } catch (err) {
      console.error(err);
      alert("Billing error.");
    } finally {
      setIsApplyingBilling(false);
    }
  };

  // ---------------------------------------------------------------------------
  // GLOBAL DOMAIN BLACKLIST HANDLERS
  // ---------------------------------------------------------------------------
  const handleAddBlacklistRule = async (e) => {
    if (e) e.preventDefault();
    if (!newRulePattern.trim()) {
      alert("Please enter a domain or pattern.");
      return;
    }
    try {
      const resp = await fetch(`${API_BASE}/api/blacklist`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          pattern: newRulePattern.trim(),
          reason: newRuleReason.trim() || "Excluded Domain"
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({ type: "success", message: `Blacklist rule '${data.pattern}' added.` });
        setNewRulePattern("");
        setNewRuleReason("");
        fetchData();
      } else {
        alert(data.detail || "Failed to add blacklist rule.");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteBlacklistRule = async (ruleId) => {
    try {
      const resp = await fetch(`${API_BASE}/api/blacklist/${ruleId}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (resp.ok) {
        setAlertBanner({ type: "info", message: "Blacklist rule removed." });
        fetchData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  // ---------------------------------------------------------------------------
  // IMAP BOUNCE & REPLY POLL HANDLER
  // ---------------------------------------------------------------------------
  const handlePollImap = async () => {
    setIsPollingImap(true);
    try {
      const resp = await fetch(`${API_BASE}/api/inbox/poll`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({
          type: "info",
          message: `IMAP Poll finished: ${data.processed_count} messages inspected. Bounces & replies synchronized.`
        });
        fetchData();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsPollingImap(false);
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
              pulseState === "DISPATCHING" ? "np-pulse-dispatching" :
              pulseState === "HUNTING" ? "np-pulse-hunting" :
              pulseState === "RUNNING" ? "np-pulse-running" : "np-pulse-idle"
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
              <span>Status: <strong className={
                pulseState === 'HOT_ALERT' ? 'text-theme-danger animate-pulse' :
                pulseState === 'DISPATCHING' ? 'text-theme-warning animate-pulse' :
                pulseState === 'HUNTING' ? 'text-theme-success animate-pulse' :
                'text-theme-accent'
              }>{pulseState}</strong></span>
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
              [{timezones.germany?.is_in_send_window ? "9 AM - 5 PM WINDOW" : "QUEUED"}]
            </span>
          </div>
          <span className="text-theme-muted">|</span>
          <div className="flex items-center gap-1.5">
            <span className="text-theme-secondary">London (GMT):</span>
            <span className="font-semibold text-theme-primary">
              {timezones.united_kingdom?.current_local_time?.split(" ")[1] || "08:15:00"}
            </span>
            <span className="text-[10px] text-theme-success">
              [{timezones.united_kingdom?.is_in_send_window ? "9 AM - 5 PM WINDOW" : "QUEUED"}]
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
          onClick={() => setActiveTab("templates")}
          className={`np-nav-tab ${activeTab === "templates" ? "active" : ""}`}
        >
          <span>📝 Proposals ({templatesList.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("analytics")}
          className={`np-nav-tab ${activeTab === "analytics" ? "active" : ""}`}
        >
          <span>📈 Deliverability</span>
        </button>

        {user.role === "admin" && (
          <button
            onClick={() => setActiveTab("billing_mgmt")}
            className={`np-nav-tab ${activeTab === "billing_mgmt" ? "active" : ""}`}
          >
            <span>💳 Manual Billing</span>
          </button>
        )}

        {user.role === "admin" && (
          <button
            onClick={() => setActiveTab("blacklist_mgmt")}
            className={`np-nav-tab ${activeTab === "blacklist_mgmt" ? "active" : ""}`}
          >
            <span>🚫 Blacklist</span>
          </button>
        )}

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
            onClick={() => setActiveTab("security_settings")}
            className={`np-nav-tab ${activeTab === "security_settings" ? "active" : ""}`}
          >
            <span>⚙️ Security Profile</span>
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

              <div className="flex items-center gap-2 flex-wrap justify-end">
                {user.role === "admin" && (
                  <button
                    onClick={() => handleToggleDispatcherBypass(!dispatcherState.bypass_window)}
                    className={`btn btn-sm ${dispatcherState.bypass_window ? "btn-danger" : "btn-secondary"}`}
                    title="Toggle immediate dispatch override regardless of timezone window or weekends"
                  >
                    <span>{dispatcherState.bypass_window ? "⚡ Bypass: 24/7 FORCED" : "🕒 Window: 9-5 Local"}</span>
                  </button>
                )}
                {user.role === "admin" && (
                  <button
                    onClick={() => handleDispatchQueueNow(true)}
                    disabled={isDispatchingNow}
                    className="btn btn-primary btn-sm flex items-center gap-1.5"
                    title="Force immediate dispatch of all authorized leads"
                  >
                    <span>{isDispatchingNow ? "Dispatching..." : "⚡ Dispatch Now (Bypass Window)"}</span>
                  </button>
                )}
                {user.role === "admin" && pendingApprovals.length > 0 && (
                  <button
                    onClick={handleBatchApprove}
                    className="btn btn-warning btn-sm"
                  >
                    ✓ Batch Authorize All ({pendingApprovals.length})
                  </button>
                )}
              </div>
            </div>

            {pendingApprovals.length === 0 ? (
              <div className="np-card p-12 text-center">
                <span className="text-3xl mb-2 block">✓</span>
                <h3 className="font-semibold text-sm text-theme-primary">Gate Clear: No Pending Outreach</h3>
                <p className="text-xs text-theme-secondary mt-1">All leads reviewed or dispatched according to dynamic 9:00 AM - 5:00 PM local business window.</p>
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
                        {user.role === "admin" && (
                          <button
                            onClick={async () => {
                              await handleApproveOutreach(item.id, item.subject, item.message_body);
                              await handleDispatchQueueNow(true, item.id);
                            }}
                            className="btn btn-primary btn-sm"
                            title="Authorize and dispatch immediately outside business hours"
                          >
                            ⚡ Authorize & Send Now
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

            {mailboxes.length === 0 ? (
              <div className="np-card p-12 text-center">
                <span className="text-3xl mb-2 block">📬</span>
                <h3 className="font-semibold text-sm text-theme-primary">No Data Available: Zero Mailboxes Enrolled</h3>
                <p className="text-xs text-theme-secondary mt-1">Enroll an active SMTP inbox into the rotation pool to enable automated outreach.</p>
                <button
                  onClick={() => setIsAddMailboxOpen(true)}
                  className="btn btn-primary btn-sm mt-4"
                >
                  + Enroll Mailbox
                </button>
              </div>
            ) : (
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
            )}
          </div>
        )}

        {/* TAB: PROPOSAL TEMPLATES */}
        {activeTab === "templates" && (
          <div className="w-full max-w-6xl mx-auto space-y-5">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary flex items-center gap-2">
                  <span>📝 Multi-Service Proposal Template Pool</span>
                  <span className="badge badge-accent">ZERO SEED</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Compose custom service proposals dynamically matched to target niches with automatic variable interpolation.
                </p>
              </div>

              <button
                onClick={() => handleOpenTemplateModal(null)}
                className="btn btn-primary btn-sm flex items-center gap-1.5"
              >
                <span>+ Create Template</span>
              </button>
            </div>

            {/* Variable Interpolation Legend */}
            <div className="p-3 bg-elevated rounded-md border-theme flex flex-wrap items-center gap-2 text-xs">
              <span className="text-theme-secondary font-medium">Available Dynamic Variables:</span>
              {[
                "{{company_name}}",
                "{{niche}}",
                "{{country}}",
                "{{city}}",
                "{{tech_stack}}",
                "{{unsubscribe_link}}"
              ].map(tag => (
                <span key={tag} className="font-mono text-[11px] px-2 py-0.5 rounded bg-overlay text-theme-accent border-theme">
                  {tag}
                </span>
              ))}
            </div>

            {templatesList.length === 0 ? (
              <div className="np-card p-12 text-center">
                <span className="text-3xl mb-2 block">📝</span>
                <h3 className="font-semibold text-sm text-theme-primary">No Data Available: Zero Proposal Templates</h3>
                <p className="text-xs text-theme-secondary mt-1">
                  The system starts 100% clean with zero seed templates. Create custom service templates to match target industries.
                </p>
                <button
                  onClick={() => handleOpenTemplateModal(null)}
                  className="btn btn-primary btn-sm mt-4"
                >
                  + Create First Proposal Template
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templatesList.map((tpl) => (
                  <div key={tpl.id} className="np-card p-4 space-y-3 flex flex-col justify-between">
                    <div className="space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className="font-semibold text-sm text-theme-primary">{tpl.title}</h3>
                          <div className="flex items-center gap-1.5 mt-1">
                            <span className="badge badge-accent text-[10px]">{tpl.niche}</span>
                            {Boolean(tpl.is_default) && (
                              <span className="badge badge-gold text-[10px]">DEFAULT FALLBACK</span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleOpenTemplateModal(tpl)}
                            className="btn btn-secondary btn-sm"
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteTemplate(tpl.id)}
                            className="btn btn-danger btn-sm"
                          >
                            Delete
                          </button>
                        </div>
                      </div>

                      <div className="bg-elevated p-3 rounded border-theme text-xs font-mono space-y-1.5">
                        <div className="text-theme-secondary font-semibold">
                          Subject: <span className="text-theme-primary">{tpl.subject_template}</span>
                        </div>
                        <div className="text-theme-primary whitespace-pre-line line-clamp-4 text-[11px] border-t-theme pt-1.5">
                          {tpl.body_template}
                        </div>
                      </div>
                    </div>

                    <div className="text-[10px] font-mono text-theme-muted pt-2 border-t-theme flex justify-between">
                      <span>Niche Match: {tpl.niche}</span>
                      <span>Updated: {tpl.updated_at ? tpl.updated_at.split("T")[0] : "—"}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB: DELIVERABILITY ANALYTICS */}
        {activeTab === "analytics" && (
          <div className="w-full max-w-6xl mx-auto space-y-5">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary flex items-center gap-2">
                  <span>📈 Campaign Deliverability Analytics Dashboard</span>
                  <span className="badge badge-success">LIVE TELEMETRY</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Visual metric indicators tracking open rates, bounce suppressions, conversion events, and sender reputation.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={fetchData}
                  className="btn btn-secondary btn-sm"
                  title="Refresh metrics"
                >
                  🔄 Refresh
                </button>
                <button
                  type="button"
                  onClick={handlePollImap}
                  disabled={isPollingImap}
                  className="btn btn-primary btn-sm flex items-center gap-1.5"
                  title="Trigger background IMAP poll for bounces and replies"
                >
                  <span>{isPollingImap ? "Polling Inboxes..." : "📡 Run IMAP Poll"}</span>
                </button>
              </div>
            </div>

            {/* 4 Primary KPI Indicator Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="np-card p-4 space-y-2 border-l-4 border-l-[var(--accent)]">
                <div className="text-xs text-theme-secondary font-semibold uppercase tracking-wider">Open Rate %</div>
                <div className="text-2xl font-bold font-mono text-theme-accent">
                  {deliverabilityStats.open_rate_percent}%
                </div>
                <div className="text-[11px] text-theme-muted font-mono">
                  {deliverabilityStats.total_opened} of {deliverabilityStats.total_delivered} delivered opened
                </div>
              </div>

              <div className="np-card p-4 space-y-2 border-l-4 border-l-[var(--danger)]">
                <div className="text-xs text-theme-secondary font-semibold uppercase tracking-wider">Bounce Rate %</div>
                <div className="text-2xl font-bold font-mono text-theme-danger">
                  {deliverabilityStats.bounce_rate_percent}%
                </div>
                <div className="text-[11px] text-theme-muted font-mono">
                  {deliverabilityStats.total_bounced} bounces auto-suppressed
                </div>
              </div>

              <div className="np-card p-4 space-y-2 border-l-4 border-l-[var(--success)]">
                <div className="text-xs text-theme-secondary font-semibold uppercase tracking-wider">Conversion Rate %</div>
                <div className="text-2xl font-bold font-mono text-theme-success">
                  {deliverabilityStats.conversion_rate_percent}%
                </div>
                <div className="text-[11px] text-theme-muted font-mono">
                  {deliverabilityStats.total_replied} replies & hot opportunities
                </div>
              </div>

              <div className="np-card p-4 space-y-2 border-l-4 border-l-[var(--gold)]">
                <div className="text-xs text-theme-secondary font-semibold uppercase tracking-wider">Sent / Delivered</div>
                <div className="text-2xl font-bold font-mono text-theme-gold">
                  {deliverabilityStats.total_delivered}
                </div>
                <div className="text-[11px] text-theme-muted font-mono">
                  {deliverabilityStats.total_sent} sent, {deliverabilityStats.total_queued} held in gate
                </div>
              </div>
            </div>

            {/* Secondary Operational Telemetry */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="np-card p-5 space-y-3">
                <h3 className="font-semibold text-sm text-theme-primary pb-2 border-b-theme">
                  Sender Health & Hygiene Telemetry
                </h3>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b-theme text-theme-secondary">
                    <span>Sender Reputation Rating:</span>
                    <span className="font-bold text-theme-success">
                      {deliverabilityStats.bounce_rate_percent < 5 ? "OPTIMAL (98/100)" : "ATTENTION REQUIRED"}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme text-theme-secondary">
                    <span>Global Suppressed Entities:</span>
                    <span className="font-bold text-theme-danger">{deliverabilityStats.total_suppressed}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme text-theme-secondary">
                    <span>Enrolled Sending Mailboxes:</span>
                    <span className="font-bold text-theme-accent">{mailboxes.length} Active</span>
                  </div>
                  <div className="flex justify-between py-1 text-theme-secondary">
                    <span>Zero-Bounce Verification:</span>
                    <span className="text-theme-success font-semibold">Active DNS MX + SMTP Ping</span>
                  </div>
                </div>
              </div>

              <div className="np-card p-5 space-y-3">
                <h3 className="font-semibold text-sm text-theme-primary pb-2 border-b-theme">
                  Outreach Pipeline Status
                </h3>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b-theme text-theme-secondary">
                    <span>Held in Approval Gate:</span>
                    <span className="font-bold text-theme-warning">{pendingApprovals.length} Leads</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme text-theme-secondary">
                    <span>High-Intent Hot Inquiries:</span>
                    <span className="font-bold text-theme-danger">{hotLeads.length} Hot Leads</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme text-theme-secondary">
                    <span>Total Entities Tracked:</span>
                    <span className="font-bold text-theme-primary">{kanbanItems.length} Total</span>
                  </div>
                  <div className="flex justify-between py-1 text-theme-secondary">
                    <span>Working Hours Window:</span>
                    <span className="text-theme-accent font-semibold">9:00 AM - 5:00 PM Local Recipient (Mon-Fri)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: DYNAMIC ADMIN PROFILE */}
        {user.role === "admin" && activeTab === "security_settings" && (
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
        {user.role === "admin" && activeTab === "operator_mgmt" && (
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

            {operatorsList.length === 0 ? (
              <div className="np-card p-12 text-center">
                <span className="text-3xl mb-2 block">👥</span>
                <h3 className="font-semibold text-sm text-theme-primary">No Data Available: Zero Operators Registered</h3>
                <p className="text-xs text-theme-secondary mt-1">Issue hardware-locked credentials and license tokens to onboard your team.</p>
                <button
                  onClick={() => setIsCreateOperatorOpen(true)}
                  className="btn btn-primary btn-sm mt-4"
                >
                  + Create Operator Account
                </button>
              </div>
            ) : (
              /* Operator List Table with Fixed Columns & Horizontal Wrapper */
              <div className="np-table-wrapper">
                <table className="np-table">
                  <thead>
                    <tr>
                      <th style={{ width: "20%" }}>Operator Identity</th>
                      <th style={{ width: "8%" }}>Role</th>
                      <th style={{ width: "10%" }}>Access Status</th>
                      <th style={{ width: "14%" }}>Device Lock</th>
                      <th style={{ width: "12%" }}>Daily Quotas</th>
                      <th style={{ width: "10%" }}>Subscription Expiry</th>
                      <th style={{ width: "10%" }}>Last Login</th>
                      <th style={{ width: "16%" }} className="text-right">Actions</th>
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
                            <div className="flex items-center justify-end gap-1.5 flex-wrap">
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
                              {op.role !== "admin" && (
                                <button
                                  onClick={() => handleDeleteOperator(op)}
                                  className="btn btn-danger btn-sm"
                                  title={`Permanently delete operator account ${op.username}`}
                                >
                                  Delete
                                </button>
                              )}
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

                                <div className="pt-2 flex items-center justify-between border-t-theme">
                                  <div>
                                    {op.role !== "admin" && (
                                      <button
                                        type="button"
                                        onClick={() => handleDeleteOperator(op)}
                                        className="btn btn-danger btn-sm"
                                        title="Permanently remove operator account"
                                      >
                                        Delete Operator Account
                                      </button>
                                    )}
                                  </div>
                                  <div className="flex justify-end gap-2">
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
                                      disabled={updatingOperatorId === op.id}
                                      className="btn btn-primary btn-sm"
                                    >
                                      {updatingOperatorId === op.id ? "Saving..." : "Apply Changes"}
                                    </button>
                                  </div>
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
            )}

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
                {sessionAuditLogs.length === 0 ? (
                  <div className="text-center py-8 text-xs text-theme-muted font-mono italic">
                    No session audit records recorded yet. Activity will stream here live as operators log in and execute actions.
                  </div>
                ) : (
                  sessionAuditLogs
                    .filter(ev => {
                      if (!auditSearch) return true;
                      const q = auditSearch.toLowerCase();
                      const u = (ev.username || ev.user || "").toLowerCase();
                      const d = (ev.detail || "").toLowerCase();
                      const a = (ev.action || "").toLowerCase();
                      return u.includes(q) || d.includes(q) || a.includes(q);
                    })
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
                          <span className="font-bold text-theme-primary shrink-0">{ev.username || ev.user || "system"}</span>
                          <span className="text-theme-secondary break-words">{ev.detail}</span>
                        </div>
                        <span className="text-theme-muted text-[11px] shrink-0">
                          {ev.created_at ? ev.created_at.replace("T", " ").split(".")[0] : "Just now"}
                        </span>
                      </div>
                    ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB: MANUAL BILLING CONTROLS (SUPER ADMIN ONLY) */}
        {user.role === "admin" && activeTab === "billing_mgmt" && (
          <div className="w-full max-w-6xl mx-auto space-y-6">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary flex items-center gap-2">
                  <span>💳 Manual Billing & Subscription Lifecycle</span>
                  <span className="badge badge-purple">SUPER ADMIN</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Direct operator license extensions, custom base pricing, and automated 10% discount on 90-day plans.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              {/* Left 2 Cols: Interactive Billing Action Form */}
              <div className="lg:col-span-2 np-card p-5 space-y-4">
                <h3 className="font-semibold text-sm text-theme-primary pb-2 border-b-theme">
                  Issue / Extend Operator Subscription
                </h3>

                <form onSubmit={handleApplyBilling} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="np-label">Target Operator</label>
                      <select
                        value={billingTargetOpId}
                        onChange={(e) => setBillingTargetOpId(e.target.value)}
                        className="np-select"
                        required
                      >
                        <option value="">-- Select Operator --</option>
                        {operatorsList.map(op => (
                          <option key={op.id} value={op.id}>
                            {op.full_name || op.username} ({op.username}) - {op.role}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="np-label">Base Price ($ USD)</label>
                      <input
                        type="number"
                        step="0.01"
                        min="1"
                        value={billingBasePrice}
                        onChange={(e) => setBillingBasePrice(e.target.value)}
                        className="np-input font-mono"
                        placeholder="199.00"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="np-label">Duration Package Extender</label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {[
                        { days: 30, label: "+30 Days (1m)", discount: 0 },
                        { days: 90, label: "+90 Days (3m)", discount: 10, highlight: true },
                        { days: 180, label: "+180 Days (6m)", discount: 0 },
                        { days: 365, label: "+1 Year (12m)", discount: 0 }
                      ].map((pkg) => (
                        <button
                          key={pkg.days}
                          type="button"
                          onClick={() => setBillingDurationDays(pkg.days)}
                          className={`btn btn-sm flex-col py-2.5 h-auto ${
                            billingDurationDays === pkg.days ? 'btn-primary' : 'btn-secondary'
                          } ${pkg.highlight && billingDurationDays !== pkg.days ? 'border-[var(--accent)] text-theme-accent' : ''}`}
                        >
                          <span className="font-bold text-xs">{pkg.label}</span>
                          {pkg.discount > 0 && (
                            <span className="text-[10px] text-theme-success font-semibold mt-0.5">
                              10% Discount
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="np-label">Invoice Reference / Notes (Optional)</label>
                    <input
                      type="text"
                      value={billingNotes}
                      onChange={(e) => setBillingNotes(e.target.value)}
                      placeholder="e.g. Wire transfer ref #8841 / Corporate renewal"
                      className="np-input text-xs"
                    />
                  </div>

                  <div className="pt-2 flex justify-end">
                    <button
                      type="submit"
                      disabled={isApplyingBilling || !billingTargetOpId}
                      className="btn btn-primary btn-sm flex items-center gap-1.5"
                    >
                      {isApplyingBilling ? (
                        <span>Processing Billing...</span>
                      ) : (
                        <>
                          <span>Apply Billing & Extend</span>
                          <span>➔</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>

              {/* Right Col: Automated Price & Discount Summary */}
              <div className="np-card p-5 space-y-4 bg-elevated border-theme">
                <h3 className="font-semibold text-sm text-theme-primary pb-2 border-b-theme">
                  Automated Pricing Breakdown
                </h3>

                {(() => {
                  const base = parseFloat(billingBasePrice) || 0;
                  const days = billingDurationDays || 30;
                  const isQuarterly = days === 90;
                  const subtotal = days === 30 ? base : (days === 90 ? base * 3 : (days === 180 ? base * 6 : base * 12));
                  const discountRate = isQuarterly ? 0.10 : 0.0;
                  const discountAmt = isQuarterly ? subtotal * discountRate : 0.0;
                  const finalTotal = subtotal - discountAmt;

                  return (
                    <div className="space-y-3 text-xs font-mono">
                      <div className="flex justify-between py-1.5 border-b-theme text-theme-secondary">
                        <span>Base Rate:</span>
                        <span className="font-bold text-theme-primary">${base.toFixed(2)}/mo</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b-theme text-theme-secondary">
                        <span>Selected Duration:</span>
                        <span className="font-bold text-theme-primary">+{days} Days</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b-theme text-theme-secondary">
                        <span>Standard Subtotal:</span>
                        <span className="text-theme-primary">${subtotal.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b-theme">
                        <span className={isQuarterly ? "text-theme-success font-semibold" : "text-theme-secondary"}>
                          Discount Applied:
                        </span>
                        <span className={isQuarterly ? "text-theme-success font-bold" : "text-theme-primary"}>
                          {isQuarterly ? `-10% (-$${discountAmt.toFixed(2)})` : "$0.00"}
                        </span>
                      </div>
                      {isQuarterly && (
                        <div className="p-2 rounded bg-[var(--success-muted)] text-[11px] text-theme-success font-sans">
                          🎉 <strong>Automated 10% Savings:</strong> 90-day quarterly package incentive applied.
                        </div>
                      )}
                      <div className="flex justify-between py-2 text-sm font-bold border-t-theme pt-3">
                        <span className="text-theme-primary">Final Amount:</span>
                        <span className="text-theme-accent text-base">${finalTotal.toFixed(2)}</span>
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>

            {/* Billing Transaction History Table */}
            <div className="np-card p-5 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b-theme">
                <div>
                  <h3 className="font-semibold text-sm text-theme-primary">Manual Billing Ledger & Audit History</h3>
                  <p className="text-xs text-theme-secondary mt-0.5">
                    Immutable log of all manual duration extensions and calculated billing transactions.
                  </p>
                </div>
                <span className="badge badge-accent font-mono text-xs">{billingHistory.length} Transactions</span>
              </div>

              {billingHistory.length === 0 ? (
                <div className="p-8 text-center">
                  <span className="text-2xl mb-1 block">💳</span>
                  <h4 className="font-semibold text-xs text-theme-primary">No Data Available: Zero Billing Records</h4>
                  <p className="text-[11px] text-theme-secondary mt-0.5">Manual subscription adjustments will be logged here.</p>
                </div>
              ) : (
                <div className="np-table-wrapper">
                  <table className="np-table text-xs">
                    <thead>
                      <tr>
                        <th>Date & Time</th>
                        <th>Operator ID</th>
                        <th>Base Rate</th>
                        <th>Duration</th>
                        <th>Discount</th>
                        <th>Final Paid</th>
                        <th>New Expiration</th>
                        <th>Admin</th>
                        <th>Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {billingHistory.map((item) => (
                        <tr key={item.id}>
                          <td className="font-mono text-theme-muted">{item.created_at ? item.created_at.split(".")[0] : "—"}</td>
                          <td className="font-mono font-semibold text-theme-primary">{item.operator_id}</td>
                          <td className="font-mono text-theme-secondary">${parseFloat(item.base_price || 0).toFixed(2)}</td>
                          <td className="font-mono font-bold text-theme-accent">+{item.duration_days}d</td>
                          <td className="font-mono">
                            {item.discount_percent > 0 ? (
                              <span className="badge badge-success text-[10px]">{item.discount_percent}% OFF</span>
                            ) : (
                              <span className="text-theme-muted">None</span>
                            )}
                          </td>
                          <td className="font-mono font-bold text-theme-success">${parseFloat(item.final_price || 0).toFixed(2)}</td>
                          <td className="font-mono text-theme-primary">{item.new_expiry_date || "—"}</td>
                          <td className="font-mono text-theme-secondary">{item.created_by || "admin"}</td>
                          <td className="text-theme-muted truncate max-w-[150px]" title={item.notes || ""}>{item.notes || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB: GLOBAL DOMAIN BLACKLIST (SUPER ADMIN ONLY) */}
        {user.role === "admin" && activeTab === "blacklist_mgmt" && (
          <div className="w-full max-w-5xl mx-auto space-y-6">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary flex items-center gap-2">
                  <span>🚫 Global Domain Blacklist & Suppression Rules</span>
                  <span className="badge badge-purple">SUPER ADMIN</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Enforce wildcard exclusion patterns (e.g., *.gov, competitor domains) across all scrapers, hygiene pipelines, and outbound queues.
                </p>
              </div>
            </div>

            {/* Add Rule Form */}
            <div className="np-card p-5 space-y-3">
              <h3 className="font-semibold text-sm text-theme-primary pb-2 border-b-theme">
                Add Global Blacklist Pattern
              </h3>
              <form onSubmit={handleAddBlacklistRule} className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
                <div>
                  <label className="np-label">Domain Pattern / Wildcard</label>
                  <input
                    type="text"
                    value={newRulePattern}
                    onChange={(e) => setNewRulePattern(e.target.value)}
                    placeholder="e.g. *.gov, competitor.de, @badagency.com"
                    className="np-input font-mono text-xs"
                    required
                  />
                </div>
                <div>
                  <label className="np-label">Exclusion Reason</label>
                  <input
                    type="text"
                    value={newRuleReason}
                    onChange={(e) => setNewRuleReason(e.target.value)}
                    placeholder="e.g. Government portal, direct competitor"
                    className="np-input text-xs"
                  />
                </div>
                <div>
                  <button type="submit" className="btn btn-primary btn-sm w-full justify-center">
                    + Add Blacklist Rule
                  </button>
                </div>
              </form>
            </div>

            {/* Blacklist Rules Table */}
            <div className="np-card p-5 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b-theme">
                <h3 className="font-semibold text-sm text-theme-primary">Active Exclusion Rules</h3>
                <span className="badge badge-accent font-mono text-xs">{blacklistRules.length} Rules Enforced</span>
              </div>

              {blacklistRules.length === 0 ? (
                <div className="p-8 text-center">
                  <span className="text-2xl mb-1 block">🛡️</span>
                  <h4 className="font-semibold text-xs text-theme-primary">No Data Available: Zero Blacklist Rules</h4>
                  <p className="text-[11px] text-theme-secondary mt-0.5">Add domain patterns above to automatically reject unwanted targets.</p>
                </div>
              ) : (
                <div className="np-table-wrapper">
                  <table className="np-table text-xs">
                    <thead>
                      <tr>
                        <th>Domain / Wildcard Pattern</th>
                        <th>Reason</th>
                        <th>Created By</th>
                        <th>Added Date</th>
                        <th className="text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {blacklistRules.map((rule) => (
                        <tr key={rule.id}>
                          <td className="font-mono font-bold text-theme-accent">{rule.pattern}</td>
                          <td className="text-theme-secondary">{rule.reason || "Excluded"}</td>
                          <td className="font-mono text-theme-muted">{rule.created_by || "admin"}</td>
                          <td className="font-mono text-theme-muted">{rule.created_at ? rule.created_at.split("T")[0] : "—"}</td>
                          <td className="text-right">
                            <button
                              type="button"
                              onClick={() => handleDeleteBlacklistRule(rule.id)}
                              className="btn btn-danger btn-sm"
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 7: LICENSE & TELEMETRY MODULE */}
        {user.role === "admin" && activeTab === "license_mgmt" && (
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
                  <label className="np-label">Target Domains / Seed URLs (Optional, one per line)</label>
                  <textarea
                    rows={2}
                    value={huntTargetUrls}
                    onChange={(e) => setHuntTargetUrls(e.target.value)}
                    placeholder="https://example-contractor.de&#10;https://berlin-bau.com"
                    className="np-textarea font-mono text-xs"
                    disabled={isHunting}
                  />
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
                  Scheduled for dynamic 9:00 AM - 5:00 PM local recipient timezone.
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
                <>
                  <button
                    onClick={() => handleApproveOutreach(selectedApproval.id, approvalSubject, approvalBody)}
                    className="btn btn-warning btn-sm"
                  >
                    Authorize & Schedule (9-5 Window)
                  </button>
                  <button
                    onClick={async () => {
                      await handleApproveOutreach(selectedApproval.id, approvalSubject, approvalBody);
                      await handleDispatchQueueNow(true, selectedApproval.id);
                    }}
                    className="btn btn-primary btn-sm flex items-center gap-1"
                    title="Authorize and immediately dispatch outside business hours or on weekends"
                  >
                    <span>⚡ Authorize & Dispatch Now</span>
                  </button>
                </>
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
                    placeholder="Leave blank to auto-bind on first login"
                    className="np-input font-mono"
                  />
                  <span className="text-[10px] text-theme-muted mt-0.5 block">
                    Optional: If left blank, locks automatically to the first physical device used to log in.
                  </span>
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
                  disabled={isCreatingOperator}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" disabled={isCreatingOperator} className="btn btn-primary btn-sm">
                  {isCreatingOperator ? "Issuing License..." : "Issue License & Create"}
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
                  disabled={isResettingPassword}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" disabled={isResettingPassword} className="btn btn-primary btn-sm">
                  {isResettingPassword ? "Encrypting with Bcrypt..." : "Reset with Bcrypt"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* MODAL: PROPOSAL TEMPLATE EDITOR */}
      {isTemplateModalOpen && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-2xl">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  {editingTemplate ? "Edit Proposal Template" : "Create New Proposal Template"}
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Dynamic niche-matching proposal with automated token interpolation.
                </p>
              </div>
              <button
                onClick={() => setIsTemplateModalOpen(false)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveTemplate}>
              <div className="np-modal-body space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">Template Title</label>
                    <input
                      type="text"
                      value={tplTitle}
                      onChange={(e) => setTplTitle(e.target.value)}
                      placeholder="e.g. Commercial Tender Outreach"
                      className="np-input font-medium"
                      required
                    />
                  </div>
                  <div>
                    <label className="np-label">Target Niche / Industry</label>
                    <input
                      type="text"
                      value={tplNiche}
                      onChange={(e) => setTplNiche(e.target.value)}
                      placeholder="e.g. Commercial Construction"
                      className="np-input"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Email Subject Line</label>
                  <input
                    type="text"
                    value={tplSubject}
                    onChange={(e) => setTplSubject(e.target.value)}
                    placeholder="e.g. Commercial Capacity & Tenders // {{company_name}}"
                    className="np-input font-mono text-xs"
                    required
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="np-label mb-0">Proposal Body Content</label>
                    <span className="text-[11px] text-theme-muted">Click chips below to insert variables</span>
                  </div>

                  {/* Token Insertion Chips */}
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {[
                      "{{company_name}}",
                      "{{niche}}",
                      "{{country}}",
                      "{{city}}",
                      "{{tech_stack}}",
                      "{{unsubscribe_link}}"
                    ].map((tag) => (
                      <button
                        key={tag}
                        type="button"
                        onClick={() => handleInsertTag(tag)}
                        className="text-[11px] font-mono px-2 py-0.5 rounded bg-overlay hover:bg-hover text-theme-accent border-theme transition-colors"
                        title={`Insert ${tag}`}
                      >
                        + {tag}
                      </button>
                    ))}
                  </div>

                  <textarea
                    rows={8}
                    value={tplBody}
                    onChange={(e) => setTplBody(e.target.value)}
                    className="np-textarea font-mono text-xs"
                    placeholder="Write your dynamic proposal copy here..."
                    required
                  />
                </div>

                <div className="flex items-center gap-2 pt-2 border-t-theme">
                  <input
                    type="checkbox"
                    id="tpl-default"
                    checked={tplIsDefault}
                    onChange={(e) => setTplIsDefault(e.target.checked)}
                    className="cursor-pointer"
                  />
                  <label htmlFor="tpl-default" className="text-xs text-theme-primary cursor-pointer select-none">
                    Set as Default Fallback Template (used when no exact niche matches)
                  </label>
                </div>
              </div>

              <div className="np-modal-footer">
                <button
                  type="button"
                  onClick={() => setIsTemplateModalOpen(false)}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  {editingTemplate ? "Save Changes" : "Create Template"}
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
