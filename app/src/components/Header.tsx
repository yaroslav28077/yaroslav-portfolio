import { useEffect, useState } from 'react'

import type { Profile } from '../content/types'
import { ButtonLink } from './ButtonLink'
import styles from './Header.module.css'

export function Header({ profile }: { profile: Profile }) {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open])

  return (
    <header className={styles.header}>
      <a className={styles.brand} href="#top" aria-label={`${profile.name}, на початок сторінки`}>
        {profile.name}
      </a>

      <nav className={styles.nav} aria-label="Основна навігація">
        {profile.nav.map((item) => (
          <a key={item.id} href={`#${item.id}`}>
            {item.label}
          </a>
        ))}
        <ButtonLink href="#contacts" className={styles.cta}>
          {profile.hero.ctaDiscuss}
        </ButtonLink>
      </nav>

      <button
        type="button"
        className={styles.menuButton}
        aria-expanded={open}
        aria-controls="mobile-menu"
        onClick={() => setOpen((value) => !value)}
      >
        {open ? 'Закрити' : 'Меню'}
      </button>

      <nav id="mobile-menu" className={styles.mobileNav} aria-label="Меню" hidden={!open}>
        {profile.nav.map((item) => (
          <a key={item.id} href={`#${item.id}`} onClick={() => setOpen(false)}>
            {item.label}
          </a>
        ))}
        <ButtonLink href="#contacts">{profile.hero.ctaDiscuss}</ButtonLink>
      </nav>
    </header>
  )
}
