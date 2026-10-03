import type { Profile, Project } from '../content/types'
import styles from './About.module.css'

export function About({ profile, projects }: { profile: Profile; projects: readonly Project[] }) {
  const { about } = profile
  return (
    <section id="about" className={styles.section} aria-labelledby="about-title">
      <div className={styles.main}>
        <h2 id="about-title" className={styles.title}>
          {about.title}
        </h2>
        {about.paragraphs.map((text) => (
          <p key={text} className={styles.paragraph}>
            {text}
          </p>
        ))}
      </div>
      <div className={styles.side}>
        <ul className={styles.facts}>
          {about.facts.map((fact) => (
            <li key={fact}>{fact}</li>
          ))}
        </ul>
        <h3 className={styles.linksTitle}>Опубліковані сайти можна перевірити самостійно</h3>
        <ul className={styles.links}>
          {projects.map((project) => (
            <li key={project.id}>
              <a href={project.url} target="_blank" rel="noopener">
                {project.host}
                <span className="visually-hidden"> (нова вкладка)</span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
