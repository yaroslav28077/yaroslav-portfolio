export interface Shot {
  readonly src: string
  readonly width: number
  readonly height: number
  readonly alt: string
}

export interface Project {
  readonly id: string
  /** Повна назва (підпис, заголовок кейсу) */
  readonly title: string
  /** Коротка назва для підпису на картці віяла (повна назва з'являється в підписі вибраної роботи) */
  readonly cardTitle: string
  /** Тип роботи: офіційний сайт, PWA тощо */
  readonly kind: string
  /** Замовник. Відсутній, якщо власник його не вказав */
  readonly client?: string
  readonly summary: string
  readonly role: string
  /** Технологія. Відсутня, якщо стек не підтверджено */
  readonly stack?: string
  readonly url: string
  readonly host: string
  readonly linkLabel: string
  /** Великий кейс чи компактніший (обидва з повноцінними прев'ю) */
  readonly featured: boolean
  readonly desktop: Shot
  readonly mobile: Shot
}

export interface NavItem {
  readonly id: string
  readonly label: string
}

export interface TitledText {
  readonly title: string
  readonly text: string
}

export interface Profile {
  readonly name: string
  readonly role: string
  readonly telegram: string
  readonly email: string
  readonly hero: {
    readonly headline: string
    readonly lead: string
    readonly ctaWorks: string
    readonly ctaDiscuss: string
  }
  readonly nav: readonly NavItem[]
  readonly works: { readonly title: string; readonly intro: string }
  readonly services: { readonly title: string; readonly intro: string; readonly items: readonly TitledText[] }
  readonly approach: { readonly title: string; readonly intro: string; readonly steps: readonly TitledText[] }
  readonly about: { readonly title: string; readonly paragraphs: readonly string[]; readonly facts: readonly string[] }
  readonly contacts: { readonly title: string; readonly text: string; readonly telegramLabel: string }
}
