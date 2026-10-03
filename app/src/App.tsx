import { About } from './components/About'
import { Approach } from './components/Approach'
import { Contacts } from './components/Contacts'
import { Footer } from './components/Footer'
import { Header } from './components/Header'
import { Hero } from './components/Hero'
import { Services } from './components/Services'
import { Works } from './components/Works'
import { profile } from './content/profile'
import { projects } from './content/projects'

export function App() {
  return (
    <div id="top">
      <a className="skip-link" href="#works">
        Перейти до робіт
      </a>
      <Header profile={profile} />
      <main>
        <Hero profile={profile} projects={projects} />
        <Works profile={profile} projects={projects} />
        <Services profile={profile} />
        <Approach profile={profile} />
        <About profile={profile} projects={projects} />
        <Contacts profile={profile} />
      </main>
      <Footer profile={profile} />
    </div>
  )
}
