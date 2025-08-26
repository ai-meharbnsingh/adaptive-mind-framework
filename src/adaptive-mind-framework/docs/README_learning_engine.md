# 🧠 The Learning Engine: Online Adaptation

> [SECTION THEME: REAL-TIME ADAPTATION & SELF-OPTIMIZATION]

The Learning Engine is the component that enables the Adaptive Mind framework to move beyond simple resilience and into true antifragility. It analyzes performance data to dynamically adjust the framework's behavior, allowing it to learn from and adapt to provider degradation in real-time without human intervention.

This document outlines the architecture of the **Online Learning** component, which is responsible for real-time adjustments.

---

## 1. Core Architectural Principles

The Online Learning system is built on two fundamental principles to ensure it never compromises the framework's primary function of processing requests reliably and quickly.

1.  **Complete Decoupling:** The learning and analysis logic is completely separated from the critical request-processing path. A failure or slowdown in the learning system will have **zero impact** on the `FailoverEngine`'s ability to serve a request.
2.  **Event-Driven Communication:** All data flows from the core engine to the learning components via a non-blocking, asynchronous `EventBus`. This ensures that publishing performance data is a "fire-and-forget" operation that does not add latency to requests.

---

## 2. Data Flow and Component Responsibilities

The online learning process is a one-way data flow that feeds a stateful ranking engine.

```mermaid
flowchart TD
    subgraph "Critical Request Path (Synchronous)"
        A[External Request] --> FE{FailoverEngine};
        FE --> |Completes Request| FB[finally block];
    end

    subgraph "Learning Path (Asynchronous)"
        EB[EventBus] --> OLS(OnlineLearningSubscriber);
        OLS --> PRE(ProviderRankingEngine);
    end

    FB -- publishes --> EB;

    style FE fill:#bbf,stroke:#333,stroke-width:2px
    style OLS fill:#cfc,stroke:#333,stroke-width:2px
    style PRE fill:#f9f,stroke:#333,stroke-width:2px