import { useState, useCallback } from 'react'

interface Coords {
  lat: number
  lon: number
}

type LocationState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'resolved'; coords: Coords }
  | { status: 'denied' }
  | { status: 'unavailable' }

export function useLocation() {
  const [state, setState] = useState<LocationState>({ status: 'idle' })

  const request = useCallback(() => {
    if (!navigator.geolocation) {
      setState({ status: 'unavailable' })
      return
    }
    setState({ status: 'loading' })
    navigator.geolocation.getCurrentPosition(
      (pos) => setState({
        status: 'resolved',
        coords: { lat: pos.coords.latitude, lon: pos.coords.longitude }
      }),
      (err) => setState({
        status: err.code === err.PERMISSION_DENIED ? 'denied' : 'unavailable'
      }),
      { timeout: 8000 }
    )
  }, [])

  const coords = state.status === 'resolved' ? state.coords : null

  return { state, coords, request }
}
