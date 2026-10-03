import type { Profile } from '../content/types'
import { SectionHead } from './SectionHead'
import styles from './Services.module.css'

export function Services({ profile }: { profile: Profile }) {
  const { services } = profile
  return (
    <section id="services" className={styles.section} aria-labelledby="services-title">
      <SectionHead id="services-title" title={services.title} intro={services.intro} />
      <ul className={styles.list}>
        {services.items.map((item) => (
          <li key={item.title} className={styles.item}>
            <h3 className={styles.name}>{item.title}</h3>
            <p className={styles.text}>{item.text}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
