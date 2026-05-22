import {
  Presentation,
  PresentationFile,
  column,
  row,
  grid,
  panel,
  text,
  shape,
  rule,
  fill,
  fixed,
  hug,
  wrap,
  fr,
} from "@oai/artifact-tool";
import { stroke } from "@oai/artifact-tool/presentation-jsx";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const OUT = "E:/Dev2/kai-cmo-harness-work/workspace/demo-clients/northstar-media-lab/presentation/output";
const PREVIEWS = "E:/Dev2/kai-cmo-harness-work/workspace/demo-clients/northstar-media-lab/presentation/previews";
const W = 1920;
const H = 1080;

const c = {
  ink: "#111827",
  muted: "#5B6472",
  line: "#D7DEE8",
  paper: "#F7F4EE",
  white: "#FFFFFF",
  blue: "#2563EB",
  coral: "#F05A4F",
  green: "#0F9F6E",
  gold: "#E1A32A",
  slate: "#263241",
  paleBlue: "#DDEBFF",
  paleCoral: "#FFE3DE",
  paleGreen: "#DDF6EB",
  paleGold: "#FFF1CB",
};

const titleStyle = { fontFamily: "Aptos Display", fontSize: 54, bold: true, color: c.ink };
const h1Style = { fontFamily: "Aptos Display", fontSize: 82, bold: true, color: c.ink };
const bodyStyle = { fontFamily: "Aptos", fontSize: 26, color: c.muted };
const smallStyle = { fontFamily: "Aptos", fontSize: 18, color: c.muted };
const labelStyle = { fontFamily: "Aptos", fontSize: 18, bold: true, color: c.ink };
const hairline = stroke(c.line);

const presentation = Presentation.create({ slideSize: { width: W, height: H } });

function compose(slide, node) {
  slide.compose(node, { frame: { left: 0, top: 0, width: W, height: H }, baseUnit: 8 });
}

function addSlide(node) {
  const slide = presentation.slides.add();
  compose(slide, node);
  return slide;
}

function pill(label, fillColor, textColor = c.ink) {
  return panel(
    {
      name: `pill-${label}`.replaceAll(" ", "-").toLowerCase(),
      fill: fillColor,
      padding: { x: 18, y: 9 },
      borderRadius: "rounded-full",
    },
    text(label, { width: fixed(116), height: hug, style: { ...labelStyle, fontSize: 17, color: textColor } }),
  );
}

function stage(name, trigger, color, purpose) {
  return column(
    { name: `stage-${name}`, width: fill, height: hug, gap: 12 },
    [
      row({ width: fill, height: hug, gap: 12, align: "center" }, [
        shape({ width: fixed(14), height: fixed(14), fill: color, geometry: "ellipse" }),
        text(name, { width: fill, height: hug, style: { ...labelStyle, fontSize: 24 } }),
      ]),
      text(trigger, { width: fill, height: hug, style: { ...smallStyle, color } }),
      text(purpose, { width: fill, height: hug, style: { ...smallStyle, fontSize: 17, color: c.muted } }),
    ],
  );
}

function emailArtifact(title, subject, preview, body, cta) {
  return panel(
    { name: `email-${title}`, fill: c.white, line: hairline, padding: { x: 32, y: 26 } },
    column(
      { width: fill, height: hug, gap: 14 },
      [
        text(title, { width: fill, height: hug, style: { ...labelStyle, fontSize: 22, color: c.blue } }),
        rule({ width: fill, stroke: c.line, weight: 2 }),
        text(`Subject: ${subject}`, { width: fill, height: hug, style: { ...labelStyle, fontSize: 20 } }),
        text(preview, { width: fill, height: hug, style: { ...smallStyle, fontSize: 17 } }),
        text(body, { width: fill, height: hug, style: { ...bodyStyle, fontSize: 22, color: c.ink } }),
        row({ width: fill, height: hug, gap: 12, align: "center" }, [
          shape({ width: fixed(10), height: fixed(10), fill: c.coral, geometry: "ellipse" }),
          text(`CTA: ${cta}`, { width: fill, height: hug, style: { ...labelStyle, fontSize: 19, color: c.coral } }),
        ]),
      ],
    ),
  );
}

// 1. Cover
addSlide(
  grid(
    {
      name: "cover-root",
      width: fill,
      height: fill,
      columns: [fr(0.9), fr(1.1)],
      rows: [fr(1)],
      padding: { x: 88, y: 72 },
      columnGap: 64,
    },
    [
      column({ width: fill, height: fill, gap: 28, justify: "center" }, [
        text("Kai CMO Harness", { width: fill, height: hug, style: { ...labelStyle, color: c.coral, fontSize: 26 } }),
        text("From blank agency brief to working email system", { name: "cover-title", width: fill, height: hug, style: h1Style }),
        text("Demo client: Northstar Media Lab, a Facebook ads agency for local service companies.", {
          name: "cover-subtitle",
          width: wrap(760),
          height: hug,
          style: { ...bodyStyle, fontSize: 30 },
        }),
        row({ width: fill, height: hug, gap: 14 }, [
          pill("Brand", c.paleCoral),
          pill("Map", c.paleBlue),
          pill("Emails", c.paleGreen),
          pill("Loops", c.paleGold),
        ]),
      ]),
      column({ width: fill, height: fill, gap: 18, justify: "center" }, [
        row({ width: fill, height: fixed(82), gap: 18 }, [
          shape({ width: fixed(260), height: fill, fill: c.coral }),
          shape({ width: fill, height: fill, fill: c.slate }),
        ]),
        row({ width: fill, height: fixed(82), gap: 18 }, [
          shape({ width: fill, height: fill, fill: c.blue }),
          shape({ width: fixed(210), height: fill, fill: c.gold }),
        ]),
        row({ width: fill, height: fixed(82), gap: 18 }, [
          shape({ width: fixed(360), height: fill, fill: c.green }),
          shape({ width: fill, height: fill, fill: c.paper, line: hairline }),
        ]),
        text("audit.requested -> audit.completed -> diagnostic.booked -> client.signed -> weekly.report.ready", {
          width: fill,
          height: hug,
          style: { ...smallStyle, fontSize: 21, color: c.slate },
        }),
      ]),
    ],
  ),
);

// 2. What Kai produced
addSlide(
  column(
    { name: "output-root", width: fill, height: fill, padding: { x: 86, y: 64 }, gap: 34 },
    [
      text("Kai turns an unmapped agency into an installable email system", { name: "slide-title", width: fill, height: hug, style: titleStyle }),
      grid({ width: fill, height: fill, columns: [fr(1), fr(1), fr(1)], rows: [fr(1), fr(1)], columnGap: 26, rowGap: 26 }, [
        panel({ fill: c.white, line: hairline, padding: { x: 30, y: 26 } }, column({ width: fill, height: hug, gap: 14 }, [
          text("1", { style: { ...h1Style, fontSize: 54, color: c.coral } }),
          text("Brand bible", { width: fill, height: hug, style: { ...labelStyle, fontSize: 26 } }),
          text("ICP, buyer language, offer, segments, demo metrics, and voice rules.", { width: fill, style: bodyStyle }),
        ])),
        panel({ fill: c.white, line: hairline, padding: { x: 30, y: 26 } }, column({ width: fill, height: hug, gap: 14 }, [
          text("2", { style: { ...h1Style, fontSize: 54, color: c.blue } }),
          text("Lifecycle map", { width: fill, height: hug, style: { ...labelStyle, fontSize: 26 } }),
          text("12 emails tied to Loops events, stage, priority, and audience segment.", { width: fill, style: bodyStyle }),
        ])),
        panel({ fill: c.white, line: hairline, padding: { x: 30, y: 26 } }, column({ width: fill, height: hug, gap: 14 }, [
          text("3", { style: { ...h1Style, fontSize: 54, color: c.green } }),
          text("Templates", { width: fill, height: hug, style: { ...labelStyle, fontSize: 26 } }),
          text("Templates for audit, sales, onboarding, retention, referral, and win-back.", { width: fill, style: bodyStyle }),
        ])),
        panel({ fill: c.white, line: hairline, padding: { x: 30, y: 26 } }, column({ width: fill, height: hug, gap: 14 }, [
          text("4", { style: { ...h1Style, fontSize: 54, color: c.gold } }),
          text("Gates", { width: fill, height: hug, style: { ...labelStyle, fontSize: 26 } }),
          text("Subject, preview, body length, banned-word, and slop checks recorded.", { width: fill, style: bodyStyle }),
        ])),
        panel({ fill: c.white, line: hairline, padding: { x: 30, y: 26 } }, column({ width: fill, height: hug, gap: 14 }, [
          text("5", { style: { ...h1Style, fontSize: 54, color: c.slate } }),
          text("Loops", { width: fill, height: hug, style: { ...labelStyle, fontSize: 26 } }),
          text("Events, segments, custom fields, and sequence flow notes ready for build.", { width: fill, style: bodyStyle }),
        ])),
        panel({ fill: c.slate, padding: { x: 30, y: 26 } }, column({ width: fill, height: hug, gap: 14 }, [
          text("Demo point", { width: fill, height: hug, style: { ...labelStyle, fontSize: 26, color: c.white } }),
          text("The output is not just copy. It is the operating logic around the copy.", { width: fill, style: { ...bodyStyle, color: "#E7ECF3" } }),
        ])),
      ]),
    ],
  ),
);

// 3. Lifecycle map
addSlide(
  column(
    { width: fill, height: fill, padding: { x: 82, y: 60 }, gap: 30 },
    [
      text("The map keeps every email attached to behavior", { name: "slide-title", width: fill, height: hug, style: titleStyle }),
      grid({ width: fill, height: fill, columns: [fr(1), fr(1), fr(1), fr(1)], rows: [fr(1), fr(1)], columnGap: 34, rowGap: 34 }, [
        stage("Welcome", "audit.requested", c.coral, "Confirm request and ask for service context."),
        stage("Nurture", "audit.completed", c.blue, "Deliver score and expose the booked-call gap."),
        stage("Sales", "proposal.sent", c.gold, "Turn audit interest into a clear buying decision."),
        stage("Onboarding", "client.signed", c.green, "Collect access and prepare the first test."),
        stage("Activation", "first.test.live", c.green, "Show what is live and what gets measured."),
        stage("Retention", "weekly.report.ready", c.blue, "Make reporting a decision rhythm."),
        stage("Referral", "client.milestone.90d", c.coral, "Ask after account health is visible."),
        stage("Win-back", "prospect.inactive_30d", c.slate, "Restart or cleanly close stalled prospects."),
      ]),
      text("Each trigger is a Loops event name, so the strategy can be installed without translating it again.", { width: fill, height: hug, style: { ...bodyStyle, fontSize: 24 } }),
    ],
  ),
);

// 4. Lead-to-call flow
addSlide(
  grid(
    { width: fill, height: fill, padding: { x: 82, y: 62 }, columns: [fr(0.95), fr(1.05)], columnGap: 56 },
    [
      column({ width: fill, height: fill, gap: 28, justify: "center" }, [
        text("Lead-to-call flow", { width: fill, height: hug, style: titleStyle }),
        text("The first sequence moves the owner from curiosity to a 30-minute diagnostic call.", { width: fill, height: hug, style: { ...bodyStyle, fontSize: 30 } }),
        row({ width: fill, height: hug, gap: 14 }, [pill("P0", c.paleCoral), pill("Audit lead", c.paleBlue), pill("Sales-qualified", c.paleGold)]),
        text("The copy keeps returning to the same business question: did Facebook create booked-call signal or only form fills?", {
          width: fill,
          height: hug,
          style: { ...bodyStyle, color: c.ink, fontSize: 32 },
        }),
      ]),
      column({ width: fill, height: fill, gap: 18, justify: "center" }, [
        stage("Audit request received", "audit.requested", c.coral, "Confirm queue and ask for service area + job value."),
        rule({ width: fixed(220), stroke: c.line, weight: 3 }),
        stage("Your audit score is ready", "audit.completed", c.blue, "Deliver scorecard and identify three spend leaks."),
        rule({ width: fixed(220), stroke: c.line, weight: 3 }),
        stage("Book the diagnostic", "audit.opened_no_call_24h", c.gold, "Turn engaged readers into a test-plan call."),
      ]),
    ],
  ),
);

// 5. Example email
addSlide(
  grid(
    { width: fill, height: fill, padding: { x: 78, y: 58 }, columns: [fr(0.85), fr(1.15)], columnGap: 44 },
    [
      column({ width: fill, height: fill, gap: 24, justify: "center" }, [
        text("Example template: audit score ready", { width: fill, height: hug, style: titleStyle }),
        text("Kai writes the message as a business decision, not a generic nurture email.", { width: fill, height: hug, style: { ...bodyStyle, fontSize: 30 } }),
        rule({ width: fixed(260), stroke: c.coral, weight: 5 }),
        text("Use this slide to show how one template carries trigger, segment, subject variants, preview text, body, CTA, and gate results.", {
          width: fill,
          height: hug,
          style: { ...bodyStyle, fontSize: 25 },
        }),
      ]),
      emailArtifact(
        "Your audit score is ready",
        "Your audit score is ready",
        "Your scorecard shows the first fixes we would make this week.",
        "The score is not a grade on your business. It is a map of where the ad account asks you to trust weak signals. The fastest fix is not a bigger budget. It is a cleaner test.",
        "Book the 30-minute diagnostic call.",
      ),
    ],
  ),
);

// 6. Client system
addSlide(
  column(
    { width: fill, height: fill, padding: { x: 84, y: 62 }, gap: 34 },
    [
      text("After the sale, the emails switch from persuasion to operation", { width: fill, height: hug, style: titleStyle }),
      grid({ width: fill, height: fill, columns: [fr(1), fr(1), fr(1)], columnGap: 30 }, [
        panel({ fill: c.paleGreen, padding: { x: 34, y: 30 } }, column({ width: fill, height: hug, gap: 18 }, [
          text("Access", { width: fill, height: hug, style: { ...labelStyle, fontSize: 30 } }),
          text("Collect Meta, pixel, CRM, call tracking, service line, and service area before spend moves.", { width: fill, style: { ...bodyStyle, color: c.ink } }),
          text("Trigger: client.signed", { style: { ...smallStyle, color: c.green } }),
        ])),
        panel({ fill: c.paleBlue, padding: { x: 34, y: 30 } }, column({ width: fill, height: hug, gap: 18 }, [
          text("Kickoff", { width: fill, height: hug, style: { ...labelStyle, fontSize: 30 } }),
          text("Frame the call around four decisions: service line, area, buyer belief, and qualified lead definition.", { width: fill, style: { ...bodyStyle, color: c.ink } }),
          text("Trigger: kickoff.scheduled", { style: { ...smallStyle, color: c.blue } }),
        ])),
        panel({ fill: c.paleGold, padding: { x: 34, y: 30 } }, column({ width: fill, height: hug, gap: 18 }, [
          text("Weekly report", { width: fill, height: hug, style: { ...labelStyle, fontSize: 30 } }),
          text("Turn reporting into next-week action: spend, qualified calls, and creative test decision.", { width: fill, style: { ...bodyStyle, color: c.ink } }),
          text("Trigger: weekly.report.ready", { style: { ...smallStyle, color: c.gold } }),
        ])),
      ]),
      text("This is the shift prospects feel: the agency stops selling and starts running the operating cadence.", { width: fill, height: hug, style: { ...bodyStyle, fontSize: 27 } }),
    ],
  ),
);

// 7. Loops build notes
addSlide(
  column(
    { width: fill, height: fill, padding: { x: 82, y: 60 }, gap: 28 },
    [
      text("Loops setup comes out with the copy", { width: fill, height: hug, style: titleStyle }),
      text("The implementation note lists what the operator needs to build the system.", { width: fill, height: hug, style: { ...bodyStyle, fontSize: 29 } }),
      grid({ width: fill, height: fill, columns: [fr(1), fr(1)], rows: [fr(1), fr(1)], columnGap: 30, rowGap: 24 }, [
        panel({ fill: c.slate, padding: { x: 30, y: 24 } }, column({ width: fill, height: hug, gap: 11 }, [
          text("Events", { width: fill, height: hug, style: { ...labelStyle, fontSize: 25, color: c.white } }),
          text("audit.requested\nproposal.sent\nclient.signed\nweekly.report.ready\nprospect.inactive_30d", {
            width: fill,
            height: hug,
            style: { fontFamily: "Consolas", fontSize: 21, color: "#E7ECF3" },
          }),
        ])),
        panel({ fill: c.white, line: hairline, padding: { x: 30, y: 26 } }, column({ width: fill, height: hug, gap: 12 }, [
          text("Segments", { width: fill, height: hug, style: { ...labelStyle, fontSize: 26 } }),
          text("Audit lead, sales-qualified prospect, proposal open, new client, active client, inactive prospect.", { width: fill, style: bodyStyle }),
        ])),
        panel({ fill: c.white, line: hairline, padding: { x: 30, y: 26 } }, column({ width: fill, height: hug, gap: 12 }, [
          text("Fields", { width: fill, height: hug, style: { ...labelStyle, fontSize: 26 } }),
          text("service_area, average_job_value, primary_service_line, audit_score, proposal_url, weekly_report_url.", { width: fill, style: bodyStyle }),
        ])),
        panel({ fill: c.white, line: hairline, padding: { x: 30, y: 26 } }, column({ width: fill, height: hug, gap: 12 }, [
          text("Rules", { width: fill, height: hug, style: { ...labelStyle, fontSize: 26 } }),
          text("Transactional messages stay tied to service events. Marketing emails need unsubscribe handling.", { width: fill, style: bodyStyle }),
        ])),
      ]),
    ],
  ),
);

// 8. Quality gates
addSlide(
  column(
    { width: fill, height: fill, padding: { x: 86, y: 64 }, gap: 36 },
    [
      text("Quality gates make the demo feel like a system, not a writing session", { width: fill, height: hug, style: titleStyle }),
      grid({ width: fill, height: fixed(420), columns: [fr(1), fr(1), fr(1), fr(1)], columnGap: 26 }, [
        panel({ fill: c.paleCoral, padding: { x: 28, y: 28 } }, column({ width: fill, height: hug, gap: 12 }, [
          text("12", { style: { ...h1Style, fontSize: 82, color: c.coral } }),
          text("email templates", { style: { ...labelStyle, fontSize: 24 } }),
        ])),
        panel({ fill: c.paleGreen, padding: { x: 28, y: 28 } }, column({ width: fill, height: hug, gap: 12 }, [
          text("12", { style: { ...h1Style, fontSize: 82, color: c.green } }),
          text("passed local gates", { style: { ...labelStyle, fontSize: 24 } }),
        ])),
        panel({ fill: c.paleBlue, padding: { x: 28, y: 28 } }, column({ width: fill, height: hug, gap: 12 }, [
          text("0", { style: { ...h1Style, fontSize: 82, color: c.blue } }),
          text("banned words", { style: { ...labelStyle, fontSize: 24 } }),
        ])),
        panel({ fill: c.paleGold, padding: { x: 28, y: 28 } }, column({ width: fill, height: hug, gap: 12 }, [
          text("200+", { width: fill, height: hug, style: { ...h1Style, fontSize: 76, color: c.gold } }),
          text("body words", { width: fill, height: hug, style: { ...labelStyle, fontSize: 24 } }),
        ])),
      ]),
      text("Four U's scoring is included as a manual demo score because the local Gemini key is not configured. The other gate scripts were run against the files.", {
        width: wrap(1360),
        height: hug,
        style: { ...bodyStyle, fontSize: 28, color: c.ink },
      }),
      text("Use this slide to explain that Kai catches weak language before the operator ships or installs anything.", { width: fill, height: hug, style: { ...bodyStyle, fontSize: 25 } }),
    ],
  ),
);

// 9. Close
addSlide(
  grid(
    { width: fill, height: fill, padding: { x: 88, y: 72 }, columns: [fr(1.05), fr(0.95)], columnGap: 58 },
    [
      column({ width: fill, height: fill, gap: 28, justify: "center" }, [
        text("The point: Kai converts marketing work into an operating artifact", { width: fill, height: hug, style: h1Style }),
        text("Strategy becomes map. Map becomes templates. Templates pass gates. The result is ready for an operator to install.", {
          width: wrap(860),
          height: hug,
          style: { ...bodyStyle, fontSize: 32 },
        }),
      ]),
      column({ width: fill, height: fill, gap: 22, justify: "center" }, [
        stage("Open during demo", "MARKETING.md", c.coral, "Show how the fictional client gets a brand bible."),
        stage("Then show", "emails/_email-system-map.md", c.blue, "The control layer for all templates."),
        stage("Then show", "emails/nurture/audit-score-ready.md", c.gold, "A real Loops-ready email example."),
        stage("Close on", "emails/_loops-setup.md", c.green, "Events, fields, segments, and flow notes."),
      ]),
    ],
  ),
);

await mkdir(OUT, { recursive: true });
await mkdir(PREVIEWS, { recursive: true });

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(path.join(OUT, "northstar-email-system-demo.pptx"));

for (let i = 0; i < presentation.slides.count; i += 1) {
  const slide = presentation.slides.getItem(i);
  const png = await slide.export({ format: "png" });
  await writeFile(path.join(PREVIEWS, `slide-${String(i + 1).padStart(2, "0")}.png`), Buffer.from(await png.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await writeFile(path.join(PREVIEWS, `slide-${String(i + 1).padStart(2, "0")}.layout.json`), JSON.stringify(layout, null, 2));
}

console.log(`Exported ${presentation.slides.count} slides.`);
console.log(path.join(OUT, "northstar-email-system-demo.pptx"));
