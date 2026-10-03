import type { Profile } from '../content/types'
import styles from './Footer.module.css'

export function Footer({ profile }: { profile: Profile }) {
  return (
    <footer className={styles.footer}>
      <p className={styles.who}>
        {profile.name}, {profile.role}
      </p>
      <nav className={styles.nav} aria-label="Навігація в підвалі">
        {profile.nav.map((item) => (
          <a key={item.id} href={`#${item.id}`}>
            {item.label}
          </a>
        ))}
      </nav>
      <p className={styles.contacts}>
        <a href={profile.telegram} target="_blank" rel="noopener">
          Telegram<span className="visually-hidden"> (нова вкладка)</span>
        </a>
        <a href={`mailto:${profile.email}`}>{profile.email}</a>
      </p>
    </footer>
  )
}
