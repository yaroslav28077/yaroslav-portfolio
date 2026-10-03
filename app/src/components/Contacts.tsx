import type { Profile } from '../content/types'
import { ButtonLink } from './ButtonLink'
import styles from './Contacts.module.css'

export function Contacts({ profile }: { profile: Profile }) {
  const { contacts } = profile
  return (
    <section id="contacts" className={styles.section} aria-labelledby="contacts-title">
      <h2 id="contacts-title" className={styles.title}>
        {contacts.title}
      </h2>
      <p className={styles.text}>{contacts.text}</p>
      <div className={styles.links}>
        <ButtonLink href={profile.telegram} variant="inverse" external hiddenSuffix="(нова вкладка)">
          {contacts.telegramLabel}
        </ButtonLink>
        <ButtonLink href={`mailto:${profile.email}`} variant="inverseLine">
          {profile.email}
        </ButtonLink>
      </div>
    </section>
  )
}
