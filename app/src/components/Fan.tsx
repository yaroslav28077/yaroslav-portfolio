import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { ComponentType, CSSProperties, FocusEvent, KeyboardEvent, UIEvent } from 'react'

import type { Project } from '../content/types'
import { cx } from '../lib/cx'
import { useMediaQuery } from '../lib/useMediaQuery'
import { FAN_ANGLES } from './fanAngles'
import type { FanSceneProps } from './fanSceneTypes'
import styles from './Fan.module.css'
import { SceneBoundary } from './SceneBoundary'

/**
 * Віяло. CSS-версія — основа й справжній fallback (до завантаження сцени, без WebGL, при помилці,
 * після втрати контексту, при prefers-reduced-motion). WebGL-сцена (окремий lazy chunk) вмикається
 * лише для широкої композиції (>1180 px) з точним вказівником і додається поверх тих самих DOM-кнопок.
 */
const SCENE_QUERY = '(min-width: 1181px) and (hover: hover) and (pointer: fine)'
const REDUCED_QUERY = '(prefers-reduced-motion: reduce)'
const PARAMS = new URLSearchParams(typeof window === 'undefined' ? '' : window.location.search)
const SCENE_OFF = PARAMS.get('scene') === 'off' // ?scene=off — примусово CSS-віяло (налагодження, тести)
const SCENE_DEBUG = PARAMS.has('scene-debug') // ?scene-debug — діагностичні data-атрибути сцени
const HAS_WEBGL = typeof window !== 'undefined' && 'WebGLRenderingContext' in window

/** Індекс картки для клавіш навігації або null, якщо клавіша не стосується віяла. */
function nextIndex(key: string, index: number, last: number): number | null {
  if (key === 'ArrowRight') return index === last ? 0 : index + 1
  if (key === 'ArrowLeft') return index === 0 ? last : index - 1
  if (key === 'Home') return 0
  if (key === 'End') return last
  return null
}

function describe(project: Project): string {
  return project.stack !== undefined ? `${project.kind}, ${project.stack}` : project.kind
}

export function Fan({ projects }: { projects: readonly Project[] }) {
  const [selected, setSelected] = useState(0)
  const [focused, setFocused] = useState<number | null>(null)
  const [stripIndex, setStripIndex] = useState(0)

  // 3D-сцена: модуль вантажиться лише коли режим доречний; CSS-віяло лишається, доки сцена не готова.
  const wide = useMediaQuery(SCENE_QUERY)
  const reduced = useMediaQuery(REDUCED_QUERY)
  const eligible = wide && !reduced && HAS_WEBGL && !SCENE_OFF
  const [Scene, setScene] = useState<ComponentType<FanSceneProps> | null>(null)
  const [failed, setFailed] = useState(false)
  const [sceneReady, setSceneReady] = useState(false)
  const handleFail = useCallback(() => setFailed(true), [])
  const handleSceneSelect = useCallback((index: number) => {
    sceneClicked.current = true
    window.setTimeout(() => {
      sceneClicked.current = false
    }, 0)
    setSelected(index)
  }, [])

  const captionRef = useRef<HTMLDivElement>(null)
  const showcaseRef = useRef<HTMLDivElement>(null)
  const fanRef = useRef<HTMLDivElement>(null)
  const sceneClicked = useRef(false)
  const cardRefs = useRef<(HTMLButtonElement | null)[]>([])
  const anchorRefs = useRef<(HTMLSpanElement | null)[]>([])
  const frameRef = useRef(0)

  const current = projects[selected] ?? projects[0]

  // Виносна лінія від підпису до вибраної картки: одне читання розкладки, далі один запис стилів.
  useLayoutEffect(() => {
    const caption = captionRef.current
    const showcase = showcaseRef.current
    const anchor = anchorRefs.current[selected]
    if (!caption || !showcase || !anchor) return

    const measure = () => {
      const c = caption.getBoundingClientRect()
      const a = anchor.getBoundingClientRect()
      const x = Math.min(Math.max(a.left + a.width / 2 - c.left, 28), Math.max(c.width - 28, 28))
      const length = Math.max(a.top - c.bottom, 0)
      caption.style.setProperty('--pointer-x', `${x}px`)
      caption.style.setProperty('--pointer-len', `${length}px`)
    }

    measure()
    const settle = window.setTimeout(measure, 340) // після підйому картки
    const observer = new ResizeObserver(measure)
    observer.observe(showcase)
    return () => {
      window.clearTimeout(settle)
      observer.disconnect()
    }
  }, [selected])

  useEffect(() => () => cancelAnimationFrame(frameRef.current), [])

  // Відкладене завантаження 3D-модуля: після першого малювання, у простої браузера; помилка → CSS-віяло.
  useEffect(() => {
    if (!eligible || failed || Scene) return
    let cancelled = false
    const load = () => {
      import('./FanScene')
        .then((m) => {
          if (!cancelled) setScene(() => m.FanScene)
        })
        .catch(() => {
          if (!cancelled) setFailed(true)
        })
    }
    if (typeof window.requestIdleCallback === 'function') {
      const id = window.requestIdleCallback(load, { timeout: 1500 })
      return () => {
        cancelled = true
        window.cancelIdleCallback(id)
      }
    }
    const id = window.setTimeout(load, 200)
    return () => {
      cancelled = true
      window.clearTimeout(id)
    }
  }, [eligible, failed, Scene])

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const holder = (event.target as HTMLElement).closest<HTMLElement>('[data-index]')
    if (!holder) return
    const index = Number(holder.dataset['index'])
    const next = nextIndex(event.key, index, projects.length - 1)
    if (next === null) return
    event.preventDefault()
    cardRefs.current[next]?.focus()
  }

  const onFocusIn = (event: FocusEvent<HTMLDivElement>) => {
    const holder = (event.target as HTMLElement).closest<HTMLElement>('[data-index]')
    setFocused(holder ? Number(holder.dataset['index']) : null)
  }
  const onFocusOut = () => setFocused(null)

  // Індикатор прокрутки стрічки на телефоні: стан змінюється лише при переході до іншої картки.
  const onScroll = (event: UIEvent<HTMLDivElement>) => {
    const strip = event.currentTarget
    cancelAnimationFrame(frameRef.current)
    frameRef.current = requestAnimationFrame(() => {
      const first = strip.children[0] as HTMLElement | undefined
      const second = strip.children[1] as HTMLElement | undefined
      if (!first || !second) return
      const step = second.offsetLeft - first.offsetLeft
      const index = Math.min(Math.max(Math.round(strip.scrollLeft / step), 0), projects.length - 1)
      setStripIndex((prev) => (prev === index ? prev : index))
    })
  }

  if (!current) return null

  const sceneActive = eligible && !failed && Scene !== null
  const webglActive = sceneActive && sceneReady
  const sceneState = failed ? 'failed' : !eligible ? 'css' : webglActive ? 'webgl' : 'loading'

  return (
    <div
      className={cx(styles.showcase, webglActive && styles.webgl)}
      ref={showcaseRef}
      data-scene={sceneState}
      data-selected={selected}
    >
      <div className={styles.caption} ref={captionRef} aria-live="polite">
        <div className={styles.captionText}>
          <p className={styles.captionLabel}>Вибрана робота</p>
          <p className={styles.captionName}>
            <span className={styles.nameFull}>{current.title}</span>
            <span className={styles.nameShort}>{current.cardTitle}</span>
          </p>
          <p className={styles.captionMeta}>{describe(current)}</p>
        </div>
        <a
          className={styles.captionLink}
          href={current.url}
          target="_blank"
          rel="noopener"
          aria-label={`${current.linkLabel}: ${current.host}, нова вкладка`}
        >
          <span className={styles.linkFull}>{current.linkLabel}</span>
          <span className={styles.linkShort}>Відкрити</span>
        </a>
        <span className={styles.leader} aria-hidden="true" />
      </div>

      <div
        ref={fanRef}
        className={styles.fan}
        role="group"
        aria-label="Чотири роботи: оберіть картку"
        onKeyDown={onKeyDown}
        onScroll={onScroll}
        onFocus={onFocusIn}
        onBlur={onFocusOut}
      >
        {projects.map((project, i) => (
          <button
            key={project.id}
            ref={(el) => {
              cardRefs.current[i] = el
            }}
            type="button"
            className={cx(styles.card, i === selected && styles.active)}
            style={{ '--r': `${FAN_ANGLES[i] ?? 0}deg` } as CSSProperties}
            aria-pressed={i === selected}
            data-index={i}
            // у WebGL-режимі клік мишею обробляє 3D-сцена: DOM-кнопка не має забирати фокус (інакше її «фокусний» підйом спрацює на сусідній картці)
            onMouseDown={webglActive ? (e) => e.preventDefault() : undefined}
            onClick={() => {
              // клік, уже оброблений 3D-сценою в цій же події, DOM-кнопка не дублює
              if (sceneClicked.current) return
              setSelected(i)
            }}
          >
            <span className={styles.cardTop}>{project.cardTitle}</span>
            <img src={project.mobile.src} width={project.mobile.width} height={project.mobile.height} alt="" decoding="async" />
            <span
              ref={(el) => {
                anchorRefs.current[i] = el
              }}
              className={styles.anchor}
              aria-hidden="true"
            />
          </button>
        ))}
      </div>

      {sceneActive && Scene ? (
        <div className={styles.sceneLayer} data-scene-layer aria-hidden="true">
          <SceneBoundary onError={handleFail}>
            <Scene
              projects={projects}
              selected={selected}
              focused={focused}
              hostRef={showcaseRef}
              eventRef={fanRef}
              debug={SCENE_DEBUG}
              onSelect={handleSceneSelect}
              onReady={setSceneReady}
              onFail={handleFail}
            />
          </SceneBoundary>
        </div>
      ) : null}

      <div className={styles.stripHelp}>
        <p className={styles.hint}>Гортайте картки вбік: усі чотири роботи в стрічці</p>
        <div className={styles.dots} aria-hidden="true">
          {projects.map((project, i) => (
            <span key={project.id} className={cx(styles.dot, i === stripIndex && styles.dotOn)} />
          ))}
        </div>
      </div>
    </div>
  )
}
