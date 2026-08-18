import { useCallback, useEffect, useState } from 'react'
import CreateLinkForm from './components/CreateLinkForm'
import LinksTable from './components/LinksTable'
import AnalyticsPanel from './components/AnalyticsPanel'
import { listLinks, topLinks, clicksOverTime } from './api'
import './styles.css'

export default function App() {
  const [links, setLinks] = useState([])
  const [topLinksData, setTopLinksData] = useState([])
  const [clicksOverTimeData, setClicksOverTimeData] = useState([])
  const [loadError, setLoadError] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const [linksRes, topRes, seriesRes] = await Promise.all([
        listLinks(),
        topLinks(),
        clicksOverTime(),
      ])
      setLinks(linksRes)
      setTopLinksData(topRes)
      setClicksOverTimeData(seriesRes)
      setLoadError(null)
    } catch (err) {
      setLoadError(err.message)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  return (
    <div className="app">
      <h1>URL Shortener</h1>
      {loadError && <p className="error">Could not reach the API: {loadError}</p>}
      <CreateLinkForm onCreated={refresh} />
      <LinksTable links={links} onChanged={refresh} />
      <AnalyticsPanel topLinksData={topLinksData} clicksOverTimeData={clicksOverTimeData} />
    </div>
  )
}
