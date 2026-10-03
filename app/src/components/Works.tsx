import type { Profile, Project } from '../content/types'
import { cx } from '../lib/cx'
import { ButtonLink } from './ButtonLink'
import { SectionHead } from './SectionHead'
import styles from './Works.module.css'

interface ProjectCaseProps {
  project: Project
  flip?: boolean
  compact?: boolean
}

/** Кейс із великим прев'ю комп'ютерної версії та накладеною мобільною. */
function ProjectCase({ project, flip = false, compact = false }: ProjectCaseProps) {
  const titleId = `case-${project.id}`
  return (
    <article className={cx(styles.case, flip && styles.flip, compact && styles.compact)} aria-labelledby={titleId}>
      <div className={styles.media}>
        <img
          className={styles.desktop}
          src={project.desktop.src}
          width={project.desktop.width}
          height={project.desktop.height}
          alt={project.desktop.alt}
          loading="lazy"
          decoding="async"
        />
        <img
          className={styles.phone}
          src={project.mobile.src}
          width={project.mobile.width}
          height={project.mobile.height}
          alt={project.mobile.alt}
          loading="lazy"
          decoding="async"
        />
      </div>
      <div className={styles.text}>
        <h3 id={titleId} className={styles.name}>
          {project.title}
        </h3>
        <p className={styles.kind}>{project.kind}</p>
        <p className={styles.summary}>{project.summary}</p>
        <dl className={styles.facts}>
          {project.client !== undefined ? (
            <>
              <dt>Замовник</dt>
              <dd>{project.client}</dd>
            </>
          ) : null}
          <dt>Моя роль</dt>
          <dd>{project.role}</dd>
          {project.stack !== undefined ? (
            <>
              <dt>Технологія</dt>
              <dd>{project.stack}</dd>
            </>
          ) : null}
        </dl>
        <ButtonLink href={project.url} external hiddenSuffix={`${project.host} (нова вкладка)`} className={styles.link}>
          {project.linkLabel}
        </ButtonLink>
      </div>
    </article>
  )
}

export function Works({ profile, projects }: { profile: Profile; projects: readonly Project[] }) {
  const featured = projects.filter((p) => p.featured)
  const compact = projects.filter((p) => !p.featured)
  return (
    <section id="works" className={styles.section} aria-labelledby="works-title">
      <SectionHead id="works-title" title={profile.works.title} intro={profile.works.intro} />
      {featured.map((project, i) => (
        <ProjectCase key={project.id} project={project} flip={i % 2 === 1} />
      ))}
      <div className={styles.compactGrid}>
        {compact.map((project) => (
          <ProjectCase key={project.id} project={project} compact />
        ))}
      </div>
    </section>
  )
}
