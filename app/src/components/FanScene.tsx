import { useCursor } from '@react-three/drei'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import type { ThreeEvent } from '@react-three/fiber'
import { useEffect, useMemo, useRef, useState } from 'react'
import type { RefObject } from 'react'
import { MathUtils, MeshStandardMaterial } from 'three'
import type { CanvasTexture, Group, Mesh, PerspectiveCamera } from 'three'

import { FAN_ANGLES } from './fanAngles'
import { FanController, Z_STEP } from './fanController'
import { buildCardGeometries } from './fanGeometry'
import { readFanMetrics, sameMetrics } from './fanMetrics'
import type { FanMetrics } from './fanMetrics'
import type { FanSceneProps } from './fanSceneTypes'
import { buildCardTexture } from './fanTexture'

/**
 * R3F-віяло. Камера в піксельному масштабі (1 одиниця = 1 CSS-піксель на площині карток),
 * тому картки стоять там само, де й у CSS-віялі. Рендер на вимогу: кадри лише під час руху.
 */
const FOV = 20
const AMBIENT = 1.95 // ≈ 0.62·π: у three ≥ r155 інтенсивності фізичні
const KEY = 1.55 // ≈ 0.49·π
const FOREST = '#0F4127'
const TANG = '#FF8A2B'
const CANVAS_STYLE = { position: 'absolute', inset: 0 } as const
const GL_OPTIONS = { antialias: true, alpha: true, powerPreference: 'default' } as const
const noRaycast = () => undefined

interface ContentsProps extends Omit<FanSceneProps, 'hostRef'> {
  metrics: FanMetrics
  /** на скільки центр колонки .showcase зміщений відносно центру canvas (поля canvas праворуч і ліворуч різні) */
  centerX: number
}

function SceneContents({ projects, metrics, centerX, selected, focused, debug, eventRef, onSelect, onReady, onFail }: ContentsProps) {
  const gl = useThree((s) => s.gl)
  const get = useThree((s) => s.get)
  const size = useThree((s) => s.size)
  const invalidate = useThree((s) => s.invalidate)
  const setEvents = useThree((s) => s.setEvents)

  const [textures, setTextures] = useState<readonly CanvasTexture[] | null>(null)
  const [overCard, setOverCard] = useState(false)
  const [controller] = useState(() => new FanController(projects.length, selected))
  const [bodyMaterial] = useState(() => new MeshStandardMaterial({ color: FOREST, roughness: 0.75 }))

  const cardRefs = useRef<(Group | null)[]>([])
  const haloRefs = useRef<(Mesh | null)[]>([])
  const fanRef = useRef<Group>(null)

  useCursor(overCard)

  const geometries = useMemo(() => buildCardGeometries(metrics.cardW, metrics.cardH), [metrics.cardW, metrics.cardH])
  useEffect(
    () => () => {
      geometries.body.dispose()
      geometries.face.dispose()
      geometries.halo.dispose()
    },
    [geometries],
  )
  useEffect(() => () => bodyMaterial.dispose(), [bodyMaterial])

  // Текстури: чекаємо шрифти й зображення; старі лишаються на екрані, доки не готові нові.
  useEffect(() => {
    let cancelled = false
    const aniso = gl.capabilities.getMaxAnisotropy()
    Promise.all(projects.map((p, i) => buildCardTexture(p, metrics, i, aniso)))
      .then((built) => {
        if (cancelled) built.forEach((t) => t.dispose())
        else setTextures(built)
      })
      .catch(() => {
        if (!cancelled) onFail('textures')
      })
    return () => {
      cancelled = true
    }
  }, [gl, projects, metrics, onFail])
  useEffect(() => () => textures?.forEach((t) => t.dispose()), [textures])

  // Камера: піксельний масштаб на площині z = 0.
  useEffect(() => {
    const cam = get().camera as PerspectiveCamera
    const z = size.height / 2 / Math.tan(MathUtils.degToRad(FOV / 2))
    cam.position.set(0, 0, z)
    cam.near = Math.max(z - 400, 10)
    cam.far = z + 1200
    cam.updateProjectionMatrix()
    invalidate()
  }, [get, size.height, invalidate])

  // Спільна модель вибору: стан приходить з DOM/React, сцена лише читає.
  useEffect(() => {
    controller.setSelected(selected)
    invalidate()
  }, [controller, selected, invalidate])
  useEffect(() => {
    controller.setFocused(focused)
    invalidate()
  }, [controller, focused, invalidate])

  // Події приходять з .fan, а не з canvas, тому координати вказівника рахуємо від меж canvas
  // (вбудований eventPrefix не віднімає зміщення canvas і тут дав би хибні промахи).
  useEffect(() => {
    setEvents({
      compute: (event, state) => {
        const r = state.gl.domElement.getBoundingClientRect()
        state.pointer.set(((event.clientX - r.left) / r.width) * 2 - 1, -((event.clientY - r.top) / r.height) * 2 + 1)
        state.raycaster.setFromCamera(state.pointer, state.camera)
      },
    })
  }, [setEvents])

  // М'який нахил за курсором: нативні passive-слухачі, жодного setState.
  // Слухаємо .fan (DOM-кнопки віяла): canvas ширший за колонку, сам подій не приймає (pointer-events: none).
  // По x нормалізуємо за шириною .fan (чутливість та сама, що й у вузькому canvas), по y — за висотою canvas.
  useEffect(() => {
    const src = eventRef.current
    if (!src) return
    const canvas = gl.domElement
    const clamp = (v: number) => Math.max(-1, Math.min(1, v))
    const move = (e: PointerEvent) => {
      const s = src.getBoundingClientRect()
      const c = canvas.getBoundingClientRect()
      controller.setPointer(clamp(((e.clientX - s.left) / s.width) * 2 - 1), clamp(-(((e.clientY - c.top) / c.height) * 2 - 1)), true)
      invalidate()
    }
    const leave = () => {
      controller.setPointer(0, 0, false)
      controller.setHover(-1)
      setOverCard(false)
      invalidate()
    }
    src.addEventListener('pointermove', move, { passive: true })
    src.addEventListener('pointerleave', leave, { passive: true })
    return () => {
      src.removeEventListener('pointermove', move)
      src.removeEventListener('pointerleave', leave)
    }
  }, [gl, eventRef, controller, invalidate])

  // Втрата контексту: віддаємо керування CSS-віялу.
  useEffect(() => {
    const el = gl.domElement
    const lost = (e: Event) => {
      e.preventDefault()
      onFail('context-lost')
    }
    el.addEventListener('webglcontextlost', lost)
    return () => el.removeEventListener('webglcontextlost', lost)
  }, [gl, onFail])

  // Готовність: перший кадр із текстурами намальовано → CSS-картки можна приховати.
  useEffect(() => {
    if (!textures) return
    invalidate()
    let second = 0
    const first = requestAnimationFrame(() => {
      second = requestAnimationFrame(() => onReady(true))
    })
    return () => {
      cancelAnimationFrame(first)
      cancelAnimationFrame(second)
    }
  }, [textures, invalidate, onReady])
  useEffect(() => () => onReady(false), [onReady])

  // Діагностика для автоматичних перевірок (лише з ?scene-debug).
  useEffect(() => {
    if (!debug) return
    const layer = gl.domElement.closest<HTMLElement>('[data-scene-layer]')
    if (!layer) return
    const ext = gl.getContext().getExtension('WEBGL_debug_renderer_info')
    layer.dataset['gpu'] = ext ? String(gl.getContext().getParameter(ext.UNMASKED_RENDERER_WEBGL)) : 'unknown'
    layer.dataset['dprCap'] = String(gl.getPixelRatio())
  }, [debug, gl])

  const localY = metrics.cardH * 1.15
  const pivotY = metrics.fanVisible - metrics.cardH * 1.65 - size.height / 2

  useFrame((state, delta) => {
    const moving = controller.step(Math.min(delta, 0.05))
    controller.apply(cardRefs.current, haloRefs.current, fanRef.current, localY)
    if (moving) state.invalidate()
    if (debug) {
      const layer = state.gl.domElement.closest<HTMLElement>('[data-scene-layer]')
      if (layer) {
        const info = state.gl.info
        layer.dataset['frames'] = String(info.render.frame)
        layer.dataset['calls'] = String(info.render.calls)
        layer.dataset['triangles'] = String(info.render.triangles)
        layer.dataset['textures'] = String(info.memory.textures)
        layer.dataset['geometries'] = String(info.memory.geometries)
        layer.dataset['state'] = controller.snapshot()
      }
    }
  })

  const hoverIn = (i: number) => (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation()
    controller.setHover(i)
    setOverCard(true)
    invalidate()
  }
  const hoverOut = (i: number) => () => {
    if (controller.hover === i) {
      controller.setHover(-1)
      setOverCard(false)
      invalidate()
    }
  }
  const click = (i: number) => (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation()
    onSelect(i)
  }

  return (
    <>
      <ambientLight intensity={AMBIENT} />
      <directionalLight position={[-320, 520, 700]} intensity={KEY} />
      <group position={[centerX, 0, 0]}>
        <group ref={fanRef}>
          {textures
            ? projects.map((project, i) => (
                <group key={project.id} position={[metrics.shift, pivotY, 0]} rotation={[0, 0, -MathUtils.degToRad(FAN_ANGLES[i] ?? 0)]}>
                  <group
                    ref={(el) => {
                      cardRefs.current[i] = el
                    }}
                    position={[0, localY, i * Z_STEP]}
                    onPointerOver={hoverIn(i)}
                    onPointerOut={hoverOut(i)}
                    onClick={click(i)}
                  >
                    <mesh geometry={geometries.body} material={bodyMaterial} raycast={noRaycast} />
                    <mesh geometry={geometries.face}>
                      <meshStandardMaterial map={textures[i] ?? null} roughness={0.9} metalness={0} toneMapped={false} />
                    </mesh>
                    <mesh
                      ref={(el) => {
                        haloRefs.current[i] = el
                      }}
                      geometry={geometries.halo}
                      raycast={noRaycast}
                      visible={false}
                    >
                      <meshBasicMaterial color={TANG} transparent opacity={0} depthWrite={false} toneMapped={false} />
                    </mesh>
                  </group>
                </group>
              ))
            : null}
        </group>
      </group>
    </>
  )
}

export function FanScene({ hostRef, ...rest }: FanSceneProps) {
  const [metrics, setMetrics] = useState<FanMetrics | null>(null)
  const [centerX, setCenterX] = useState(0)
  const [visible, setVisible] = useState(true)
  const rootRef = useRef<HTMLDivElement>(null)
  const count = rest.projects.length

  // Розміри з CSS: перечитуємо при зміні розкладки, а не щокадру.
  useEffect(() => {
    const host = hostRef.current
    if (!host) return
    const read = () => {
      const next = readFanMetrics(host, count)
      if (next) setMetrics((prev) => (prev && sameMetrics(prev, next) ? prev : next))
      // світова вісь x = центр canvas; поля canvas несиметричні, тож зсуваємо сцену до центру колонки
      const layer = host.querySelector('[data-scene-layer]')
      if (layer) {
        const h = host.getBoundingClientRect()
        const l = layer.getBoundingClientRect()
        setCenterX(Math.round((h.left + h.width / 2 - (l.left + l.width / 2)) * 10) / 10)
      }
    }
    read()
    const observer = new ResizeObserver(read)
    observer.observe(host)
    const layerEl = host.querySelector('[data-scene-layer]')
    if (layerEl) observer.observe(layerEl)
    return () => observer.disconnect()
  }, [hostRef, count])

  // Поза viewport сцена не малює (frameloop='never').
  useEffect(() => {
    const root = rootRef.current
    if (!root) return
    const observer = new IntersectionObserver(([entry]) => entry && setVisible(entry.isIntersecting), { threshold: 0 })
    observer.observe(root)
    return () => observer.disconnect()
  }, [])

  return (
    <div ref={rootRef} style={CANVAS_STYLE}>
      <Canvas
        frameloop={visible ? 'demand' : 'never'}
        dpr={[1, 1.5]}
        flat
        gl={GL_OPTIONS}
        camera={{ fov: FOV, position: [0, 0, 1200], near: 100, far: 4000 }}
        eventSource={rest.eventRef as RefObject<HTMLElement>}
        style={CANVAS_STYLE}
      >
        {metrics ? <SceneContents {...rest} metrics={metrics} centerX={centerX} /> : null}
      </Canvas>
    </div>
  )
}
