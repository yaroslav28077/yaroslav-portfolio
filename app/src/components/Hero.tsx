import type { Profile, Project } from '../content/types'
import { ButtonLink } from './ButtonLink'
import { Fan } from './Fan'
import styles from './Hero.module.css'

export function Hero({ profile, projects }: { profile: Profile; projects: readonly Project[] }) {
  const { hero } = profile
  return (
    <section className={styles.hero} aria-labelledby="hero-title">
      <div className={styles.copy}>
        <h1 id="hero-title" className={styles.title}>
          {hero.headline}
        </h1>
        <p className={styles.lead}>{hero.lead}</p>
        <div className={styles.cta}>
          <ButtonLink href="#works">{hero.ctaWorks}</ButtonLink>
          <ButtonLink href="#contacts" variant="line">
            {hero.ctaDiscuss}
          </ButtonLink>
        </div>
      </div>
      <Fan projects={projects} />
    </section>
  )
}
