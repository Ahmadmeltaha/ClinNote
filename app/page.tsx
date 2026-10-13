"use client";

import { PageTitle } from "@/src/components/kit/page-title";
import { Card } from "@/src/components/kit/card";
import { Button } from "@/src/components/kit/button";

export default function Home() {
  return (
    <main className="container-page">
      {/* Hero Section */}
      <section
        style={{
          paddingBlock: "var(--space-16)",
          textAlign: "center",
        }}
      >
        <h1
          style={{
            fontSize: "var(--text-display)",
            fontFamily: "var(--font-heading)",
            color: "var(--color-brand)",
            marginBottom: "var(--space-4)",
          }}
        >
          OrchState
        </h1>
        <p
          style={{
            fontSize: "var(--kit-text-section)",
            color: "var(--color-ink)",
            maxWidth: "40rem",
            marginInline: "auto",
            marginBottom: "var(--space-8)",
          }}
          className="text-wraps"
        >
          From idea to software — naturally.
        </p>
        <p
          style={{
            fontSize: "var(--kit-text-body)",
            color: "var(--color-ink)",
            maxWidth: "40rem",
            marginInline: "auto",
          }}
          className="text-wraps"
        >
          Idea to software flow
        </p>
        <div
          style={{
            maxWidth: "40rem",
            marginInline: "auto",
            marginTop: "var(--space-8)",
          }}
        >
          <svg
            role="img"
            aria-label="Idea to software flow"
            viewBox="0 0 400 120"
            style={{ width: "100%", height: "auto" }}
          >
            {/* Lightbulb (idea) */}
            <circle cx="50" cy="60" r="25" fill="var(--color-accent)" />
            <path d="M45 50 L55 50 L50 40 Z" fill="var(--color-canvas)" />
            <rect x="47" y="75" width="6" height="10" rx="2" fill="var(--color-ink-soft)" />

            {/* Arrow to describe */}
            <line
              x1="80"
              y1="60"
              x2="120"
              y2="60"
              stroke="var(--color-ink)"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />

            {/* Document (describe) */}
            <rect
              x="125"
              y="35"
              width="40"
              height="50"
              rx="4"
              fill="var(--color-brand)"
            />
            <line
              x1="132"
              y1="50"
              x2="158"
              y2="50"
              stroke="var(--color-on-brand)"
              strokeWidth="2"
            />
            <line
              x1="132"
              y1="58"
              x2="158"
              y2="58"
              stroke="var(--color-on-brand)"
              strokeWidth="2"
            />
            <line
              x1="132"
              y1="66"
              x2="150"
              y2="66"
              stroke="var(--color-on-brand)"
              strokeWidth="2"
            />

            {/* Arrow to approve */}
            <line
              x1="170"
              y1="60"
              x2="210"
              y2="60"
              stroke="var(--color-ink)"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />

            {/* Checkmark (approve) */}
            <circle cx="230" cy="60" r="25" fill="var(--color-success)" />
            <path
              d="M220 60 L227 67 L240 53"
              stroke="var(--color-on-success)"
              strokeWidth="3"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Arrow to build */}
            <line
              x1="260"
              y1="60"
              x2="300"
              y2="60"
              stroke="var(--color-ink)"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />

            {/* Code brackets (build) */}
            <rect
              x="305"
              y="35"
              width="50"
              height="50"
              rx="4"
              fill="var(--color-ink)"
            />
            <text
              x="315"
              y="65"
              fontFamily="monospace"
              fontSize="16"
              fill="var(--color-canvas)"
            >
              {"</>"}
            </text>

            {/* Arrow to review */}
            <line
              x1="360"
              y1="60"
              x2="390"
              y2="60"
              stroke="var(--color-ink)"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />

            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon points="0 0, 10 3.5, 0 7" fill="var(--color-ink)" />
              </marker>
            </defs>
          </svg>
        </div>
      </section>

      {/* What is OrchState Section */}
      <section
        style={{
          paddingBlock: "var(--space-16)",
          borderTop: "1px solid var(--color-border)",
        }}
      >
        <PageTitle>What is OrchState</PageTitle>
        <div
          style={{
            display: "flex",
            gap: "var(--space-8)",
            alignItems: "center",
            flexWrap: "wrap",
            marginTop: "var(--space-6)",
          }}
        >
          <div style={{ flex: "1 1 20rem" }}>
            <p
              style={{
                fontSize: "var(--kit-text-body)",
                color: "var(--color-ink)",
                lineHeight: 1.6,
              }}
              className="text-wraps"
            >
              OrchState is a platform that transforms your ideas into working
              software through a guided process. You describe what you want, we
              help you refine it, then automatically generate the code you need.
            </p>
          </div>
          <div
            style={{
              flex: "0 0 auto",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <svg
              role="img"
              aria-label="OrchState illustration"
              viewBox="0 0 120 120"
              style={{ width: "120px", height: "120px" }}
            >
              <circle
                cx="60"
                cy="60"
                r="50"
                fill="var(--color-canvas)"
                stroke="var(--color-brand)"
                strokeWidth="3"
              />
              <circle cx="60" cy="60" r="30" fill="var(--color-brand)" />
              <path
                d="M45 60 L55 50 L65 60 L75 50"
                stroke="var(--color-on-brand)"
                strokeWidth="4"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="40" cy="40" r="5" fill="var(--color-accent)" />
              <circle cx="80" cy="40" r="5" fill="var(--color-accent)" />
              <circle cx="60" cy="85" r="5" fill="var(--color-accent)" />
            </svg>
          </div>
        </div>
      </section>

      {/* How it Works Section */}
      <section
        style={{
          paddingBlock: "var(--space-16)",
          borderTop: "1px solid var(--color-border)",
        }}
      >
        <PageTitle>How it works</PageTitle>
        <div
          className="grid-cards"
          style={{
            marginTop: "var(--space-6)",
            gap: "var(--space-6)",
          }}
        >
          {[
            {
              step: 1,
              title: "Describe",
              desc: "Tell us what you want to build in plain language.",
              iconPath:
                "M30 40 L30 80 M30 50 L60 50 M30 60 L55 60 M30 70 L50 70",
            },
            {
              step: 2,
              title: "Approve",
              desc: "Review the plan and confirm it matches your vision.",
              iconPath:
                "M35 55 L45 65 L65 45",
            },
            {
              step: 3,
              title: "Build",
              desc: "We generate the code and infrastructure automatically.",
              iconPath:
                "M30 45 L40 55 L30 65 M70 45 L60 55 L70 65 M45 40 L55 70",
            },
            {
              step: 4,
              title: "Review",
              desc: "Test your application and iterate as needed.",
              iconPath:
                "M30 55 A25 25 0 1 0 70 55 M50 55 L50 40 M45 45 L50 40 L55 45",
            },
          ].map((item) => (
            <Card key={item.step}>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  textAlign: "center",
                  padding: "var(--space-6)",
                }}
              >
                <div
                  style={{
                    width: "60px",
                    height: "60px",
                    borderRadius: "var(--radius-full)",
                    backgroundColor: "var(--color-brand)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: "var(--space-4)",
                  }}
                >
                  <span
                    style={{
                      fontSize: "var(--kit-text-section)",
                      fontWeight: 700,
                      color: "var(--color-ink)",
                    }}
                  >
                    {item.step}
                  </span>
                </div>
                <svg
                  role="img"
                  aria-label={item.title + " icon"}
                  viewBox="0 0 100 100"
                  style={{
                    width: "50px",
                    height: "50px",
                    marginBottom: "var(--space-3)",
                  }}
                >
                  <path
                    d={item.iconPath}
                    stroke="var(--color-ink)"
                    strokeWidth="4"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <h3
                  style={{
                    fontSize: "var(--kit-text-section)",
                    fontFamily: "var(--font-heading)",
                    color: "var(--color-brand)",
                    marginBottom: "var(--space-2)",
                  }}
                >
                  {item.title}
                </h3>
                <p
                  style={{
                    fontSize: "var(--kit-text-body)",
                    color: "var(--color-ink)",
                  }}
                  className="text-wraps"
                >
                  {item.desc}
                </p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Key Features Section */}
      <section
        style={{
          paddingBlock: "var(--space-16)",
          borderTop: "1px solid var(--color-border)",
        }}
      >
        <PageTitle>Key features</PageTitle>
        <div
          className="grid-cards"
          style={{
            marginTop: "var(--space-6)",
            gap: "var(--space-6)",
          }}
        >
          {[
            {
              title: "Natural Language Input",
              desc: "Describe your idea in everyday words.",
              icon: "💬",
            },
            {
              title: "Smart Validation",
              desc: "Automatic checks ensure your plan is feasible.",
              icon: "✓",
            },
            {
              title: "Code Generation",
              desc: "Production-ready code built from your specs.",
              icon: "⚙",
            },
            {
              title: "Visual Preview",
              desc: "See your app before it goes live.",
              icon: "👁",
            },
            {
              title: "One-Click Deploy",
              desc: "Launch to the cloud with a single click.",
              icon: "☁",
            },
            {
              title: "Iterative Refinement",
              desc: "Tweak and improve with each version.",
              icon: "↺",
            },
          ].map((feature, idx) => (
            <Card key={idx}>
              <div
                style={{
                  padding: "var(--space-6)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "var(--space-3)",
                }}
              >
                <div
                  style={{
                    fontSize: "var(--kit-text-section)",
                    width: "48px",
                    height: "48px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: "var(--color-accent-soft)",
                    borderRadius: "var(--radius-card)",
                  }}
                  aria-hidden="true"
                >
                  {feature.icon}
                </div>
                <h3
                  style={{
                    fontSize: "var(--kit-text-section)",
                    fontFamily: "var(--font-heading)",
                    color: "var(--color-brand)",
                  }}
                >
                  {feature.title}
                </h3>
                <p
                  style={{
                    fontSize: "var(--kit-text-body)",
                    color: "var(--color-ink)",
                  }}
                  className="text-wraps"
                >
                  {feature.desc}
                </p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Closing Section */}
      <section
        style={{
          paddingBlock: "var(--space-16)",
          borderTop: "1px solid var(--color-border)",
          textAlign: "center",
        }}
      >
        <p
          style={{
            fontSize: "var(--kit-text-section)",
            color: "var(--color-ink)",
            maxWidth: "40rem",
            marginInline: "auto",
            marginBottom: "var(--space-6)",
          }}
          className="text-wraps"
        >
          Ready to turn your idea into reality?
        </p>
        <Button type="button" kind="primary">
          Get Started
        </Button>
      </section>
    </main>
  );
}
