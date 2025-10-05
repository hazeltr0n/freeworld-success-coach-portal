// Auto-learn city→market mappings from new job locations
// Run as Edge Function or Database Trigger

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const MARKET_CENTERS = {
  'Dallas': { zip: '75060', radius: 75 },
  'Houston': { zip: '77007', radius: 75 },
  'Phoenix': { zip: '85009', radius: 75 },
  'Denver': { zip: '80218', radius: 75 },
  'Las Vegas': { zip: '89107', radius: 75 },
  'Stockton': { zip: '95205', radius: 75 },
  'Bay Area': { zip: '94501', radius: 75 },
  'Inland Empire': { zip: '92324', radius: 75 },
  'Trenton': { zip: '07017', radius: 50 },
  'Newark': { zip: '08638', radius: 75 },
  'Sacramento': { zip: '95814', radius: 75 },
  'Rochester': { zip: '14604', radius: 75 },
  'Des Moines': { zip: '50309', radius: 75 }
}

async function getZipCoordinates(zip: string): Promise<[number, number] | null> {
  try {
    const response = await fetch(`https://api.zippopotam.us/us/${zip}`)
    if (response.ok) {
      const data = await response.json()
      if (data.places?.length > 0) {
        return [
          parseFloat(data.places[0].latitude),
          parseFloat(data.places[0].longitude)
        ]
      }
    }
  } catch (e) {
    console.error(`ZIP lookup failed for ${zip}:`, e)
  }
  return null
}

function calculateDistance(coord1: [number, number], coord2: [number, number]): number {
  // Haversine formula for distance in miles
  const [lat1, lon1] = coord1
  const [lat2, lon2] = coord2

  const R = 3959 // Earth's radius in miles
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180

  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2)

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  return R * c
}

async function determineMarkets(jobZip: string): Promise<string[]> {
  const jobCoords = await getZipCoordinates(jobZip)
  if (!jobCoords) return []

  const markets: string[] = []

  for (const [marketName, config] of Object.entries(MARKET_CENTERS)) {
    const marketCoords = await getZipCoordinates(config.zip)
    if (marketCoords) {
      const distance = calculateDistance(jobCoords, marketCoords)
      if (distance <= config.radius) {
        markets.push(marketName)
      }
    }
  }

  return markets
}

serve(async (req) => {
  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    console.log('🔍 Finding new cities from jobs...')

    // Get unique location+ZIP from jobs
    const { data: jobs, error: jobsError } = await supabase
      .from('jobs')
      .select('location, zip_code')

    if (jobsError) throw jobsError

    // Get existing locations
    const { data: existing, error: existingError } = await supabase
      .from('location_markets')
      .select('location_string')

    if (existingError) throw existingError

    const existingSet = new Set(
      existing.map(row => row.location_string.toLowerCase().trim())
    )

    // Find new locations
    const newLocations = new Map<string, string>()

    for (const job of jobs) {
      const location = job.location?.toLowerCase().trim()
      const zipCode = job.zip_code

      if (location && zipCode && !existingSet.has(location) && !newLocations.has(location)) {
        newLocations.set(location, zipCode)
      }
    }

    console.log(`🆕 Found ${newLocations.size} new locations`)

    const results = {
      added: 0,
      failed: 0,
      locations: [] as any[]
    }

    // Process each new location
    for (const [location, zipCode] of newLocations) {
      const markets = await determineMarkets(zipCode)

      if (markets.length > 0) {
        const { error: insertError } = await supabase
          .from('location_markets')
          .insert({
            location_string: location,
            location_type: 'city',
            markets: markets,
            default_zips: [zipCode]
          })

        if (insertError) {
          console.error(`Failed to add ${location}:`, insertError)
          results.failed++
        } else {
          console.log(`✅ ${location} → ${markets.join(', ')}`)
          results.added++
          results.locations.push({ location, markets, zip: zipCode })
        }
      } else {
        console.log(`❌ ${location} → No markets found`)
        results.failed++
      }

      // Rate limit API calls
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    return new Response(
      JSON.stringify({
        success: true,
        ...results
      }),
      {
        headers: { 'Content-Type': 'application/json' },
        status: 200
      }
    )

  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message
      }),
      {
        headers: { 'Content-Type': 'application/json' },
        status: 500
      }
    )
  }
})
