# Arquitectura — Clasificación de Cartera Bancaria con Google ADK

## Diagrama General

```mermaid
graph TB
    subgraph Entrada
        CSV[data/g3_cartera_clientes.csv]
    end

    subgraph "Google ADK - SequentialAgent"
        direction TB
        A1[Analista de Riesgo<br/>LlmAgent]
        A2[Estratega Comercial<br/>LlmAgent]
        A3[Auditor<br/>LlmAgent]
        
        A1 -->|output_key: resultado_analisis| A2
        A2 -->|output_key: opinion_comercial| A3
    end

    subgraph "Tools (FunctionTools)"
        T1[leer_cartera]
        T2[ejecutar_motor_reglas]
        T3[generar_reporte_auditoria]
    end

    subgraph "Motor de Reglas"
        RE[regla_engine.py<br/>7 reglas deterministas]
    end

    subgraph Salida
        OUT1[output/cartera_clasificada.csv]
        OUT2[output/reporte_auditoria.txt]
    end

    CSV --> T1
    CSV --> T2
    T1 --> A1
    T2 --> RE
    RE --> OUT1
    T2 --> A1
    A1 -.->|lee estado| A2
    A2 -.->|lee estado| A3
    A3 --> T3
    T3 --> OUT2

    style A1 fill:#4A90D9,stroke:#2E5A8B,color:#fff
    style A2 fill:#7B68EE,stroke:#4B3BA3,color:#fff
    style A3 fill:#50C878,stroke:#2E8B57,color:#fff
    style RE fill:#FFD700,stroke:#DAA520,color:#000
    style CSV fill:#E8E8E8,stroke:#A0A0A0
    style OUT1 fill:#90EE90,stroke:#228B22
    style OUT2 fill:#90EE90,stroke:#228B22
```

## Flujo de Ejecución

```mermaid
sequenceDiagram
    participant M as main.py
    participant R as InMemoryRunner
    participant P as SequentialAgent
    participant A1 as AnalistaRiesgo
    participant A2 as EstrategaComercial
    participant A3 as Auditor
    participant T as Tools
    participant E as MotorReglas

    M->>R: crear sesión
    R->>P: ejecutar pipeline
    
    P->>A1: invocar agente
    A1->>T: leer_cartera()
    T-->>A1: resumen estadístico
    A1->>T: ejecutar_motor_reglas()
    T->>E: evaluar 7 reglas
    E-->>T: cartera clasificada
    T-->>A1: distribución acciones
    A1->>P: guardar en estado[resultado_analisis]
    
    P->>A2: invocar agente
    A2->>P: leer estado[resultado_analisis]
    A2->>P: guardar en estado[opinion_comercial]
    
    P->>A3: invocar agente
    A3->>P: leer estado[opinion_comercial]
    A3->>T: generar_reporte_auditoria()
    T-->>A3: reporte formal
    A3->>P: completar pipeline
    
    P-->>R: resultado final
    R-->>M: terminar
```

## Componentes Principales

### 1. Pipeline Secuencial (SequentialAgent)

```mermaid
graph LR
    subgraph "Pipeline - Flujo de Estado"
        S1[Estado Inicial] --> A1
        A1[Analista de Riesgo] -->|output_key| S2
        S2[resultado_analisis] --> A2
        A2[Estratega Comercial] -->|output_key| S3
        S3[opinion_comercial] --> A3
        A3[Auditor] -->|output_key| S4
        S4[reporte_final]
    end

    style A1 fill:#4A90D9,color:#fff
    style A2 fill:#7B68EE,color:#fff
    style A3 fill:#50C878,color:#fff
```

### 2. Motor de Reglas Determinista

```mermaid
graph TD
    INPUT[CSV Cartera] --> PARSE[pd.read_csv]
    PARSE --> LOOP{Para cada cliente}
    
    LOOP --> R01{R01: Inversor activo<br/>alto patrimonio?}
    R01 -->|Sí| A1[Banca inversión]
    R01 -->|No| R02{R02: Premium sin<br/>inversión?}
    
    R02 -->|Sí| A1
    R02 -->|No| R03{R03: Alto ingreso<br/>sin inversión?}
    
    R03 -->|Sí| A1
    R03 -->|No| R04{R04: Capacidad<br/>hipotecaria?}
    
    R04 -->|Sí| A2[Ofrecer hipotecario]
    R04 -->|No| R05{R05: Score alto<br/>sin TC?}
    
    R05 -->|Sí| A3[Ofrecer TC]
    R05 -->|No| R06{R06: Capacidad<br/>consumo?}
    
    R06 -->|Sí| A4[Ofrecer consumo]
    R06 -->|No| R07{R07: Default}
    
    R07 -->|Default| A5[Más cupo TC]
    
    A1 --> OUT[accion_sugerida<br/>regla_aplicada<br/>justificacion]
    A2 --> OUT
    A3 --> OUT
    A4 --> OUT
    A5 --> OUT
    
    OUT --> NEXT[Siguiente cliente]
    NEXT --> LOOP

    style R01 fill:#FFD700,stroke:#DAA520
    style R02 fill:#FFD700,stroke:#DAA520
    style R03 fill:#FFD700,stroke:#DAA520
    style R04 fill:#FFD700,stroke:#DAA520
    style R05 fill:#FFD700,stroke:#DAA520
    style R06 fill:#FFD700,stroke:#DAA520
    style R07 fill:#FFD700,stroke:#DAA520
```

### 3. Stack Tecnológico

```mermaid
graph TB
    subgraph "Capa de Aplicación"
        MAIN[main.py<br/>Punto de entrada]
        PIPE[pipeline.py<br/>Orquestación]
    end
    
    subgraph "Google ADK"
        RUNNER[InMemoryRunner]
        SEQ[SequentialAgent]
        LLM[LlmAgent × 3]
        TOOL[FunctionTool]
    end
    
    subgraph "Modelo LLM"
        QWEN[Qwen 3.5 Plus<br/>vía OpenRouter]
        LITE[LiteLlm Adapter]
    end
    
    subgraph "Capa de Datos"
        PD[pandas]
        CSV[CSV Files]
    end
    
    subgraph "Lógica de Negocio"
        ENGINE[regla_engine.py<br/>Motor determinista]
        RULES[7 Reglas<br/>R01-R07]
    end
    
    MAIN --> RUNNER
    RUNNER --> SEQ
    SEQ --> LLM
    LLM --> TOOL
    TOOL --> ENGINE
    ENGINE --> RULES
    LLM --> LITE
    LITE --> QWEN
    TOOL --> PD
    PD --> CSV

    style QWEN fill:#FF6B6B,stroke:#C92A2A,color:#fff
    style ENGINE fill:#FFD700,stroke:#DAA520,color:#000
    style RUNNER fill:#4A90D9,stroke:#2E5A8B,color:#fff
```

## Catálogo de Reglas

| Código | Nombre | Acción | Prioridad |
|--------|--------|--------|-----------|
| R01 | Inversor activo de alto patrimonio | Banca de inversión | 1 |
| R02 | Premium con patrimonio líquido sin inversión | Banca de inversión | 2 |
| R03 | Alto ingreso y saldo sin inversión | Banca de inversión | 3 |
| R04 | Alta capacidad con estabilidad demostrada | Ofrecer hipotecario | 4 |
| R05 | Score alto sin tarjeta de crédito | Ofrecer TC | 5 |
| R06 | Capacidad de crédito de consumo | Ofrecer consumo | 6 |
| R07 | Default — Cliente estándar | Más cupo TC | 7 |

## Flujo de Datos

```mermaid
flowchart LR
    subgraph Input
        A[g3_cartera_clientes.csv<br/>~1000 clientes]
    end
    
    subgraph Processing
        B[Motor de Reglas<br/>Evaluación por prioridad]
        C[3 Agentes LLM<br/>Análisis + Validación + Auditoría]
    end
    
    subgraph Output
        D[cartera_clasificada.csv<br/>+3 columnas]
        E[reporte_auditoria.txt<br/>Trazabilidad completa]
    end
    
    A -->|leer_cartera| B
    B -->|ejecutar_motor_reglas| C
    C -->|generar_reporte| D
    C -->|generar_reporte| E

    style A fill:#E8E8E8,stroke:#A0A0A0
    style B fill:#FFD700,stroke:#DAA520,color:#000
    style C fill:#4A90D9,stroke:#2E5A8B,color:#fff
    style D fill:#90EE90,stroke:#228B22
    style E fill:#90EE90,stroke:#228B22
```

## Diferencias CrewAI vs Google ADK

```mermaid
flowchart TB
    subgraph CREW[CrewAI]
        direction TB
        C1["Crew + Process.sequential"]
        C2["context = tarea_anterior"]
        C3["BaseTool + Pydantic"]
        C4["kickoff() síncrono"]
    end
    
    subgraph ADK[Google ADK]
        direction TB
        A1["SequentialAgent + sub_agents"]
        A2["output_key + {variable}"]
        A3["Funciones Python puras"]
        A4["run_async() asíncrono"]
    end
    
    CREW -->|Migración| ADK

    style CREW fill:#FFB6C1,stroke:#DC143C,color:#000
    style ADK fill:#90EE90,stroke:#228B22,color:#000
```
