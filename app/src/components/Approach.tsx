import type { Profile } from '../content/types'
import { SectionHead } from './SectionHead'
import styles from './Approach.module.css'

export function Approach({ profile }: { profile: Profile }) {
  const { approach } = profile
  return (
    <section id="approach" className={styles.section} aria-labelledby="approach-title">
      <SectionHead id="approach-title" title={approach.title} intro={approach.intro} />
      <ol className={styles.steps}>
        {approach.steps.map((step, i) => (
          <li key={step.title} className={styles.step}>
            <span className={styles.number} aria-hidden="true">
              {i + 1}
            </span>
            <h3 className={styles.name}>{step.title}</h3>
            <p className={styles.text}>{step.text}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}
