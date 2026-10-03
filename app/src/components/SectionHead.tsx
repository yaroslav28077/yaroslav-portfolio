import styles from './SectionHead.module.css'

interface SectionHeadProps {
  id: string
  title: string
  intro?: string | undefined
}

export function SectionHead({ id, title, intro }: SectionHeadProps) {
  return (
    <div className={styles.head}>
      <h2 id={id} className={styles.title}>
        {title}
      </h2>
      {intro !== undefined ? <p className={styles.intro}>{intro}</p> : null}
    </div>
  )
}
