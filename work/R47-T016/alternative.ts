type TeamRecord = {
  played: number
  won: number
  drawn: number
  lost: number
}

const emptyRecord = (): TeamRecord => ({
  played: 0,
  won: 0,
  drawn: 0,
  lost: 0,
})

const formatRow = (name: string, record: TeamRecord): string => {
  const points = record.won * 3 + record.drawn
  const cells = [
    record.played,
    record.won,
    record.drawn,
    record.lost,
    points,
  ].map((value) => {
    const text = value.toString()
    return text.padStart(3 - text.length, ' ')
  })

  return `${name.padEnd(31, ' ')}| ${cells.join(' | ')}`
}

export class Tournament {
  private tableHeader =
    'Team                           | MP |  W |  D |  L |  P'

  public tally(input: string): string {
    if (!input) return this.tableHeader

    const records = new Map<string, TeamRecord>()
    const getRecord = (name: string): TeamRecord => {
      const record = records.get(name) ?? emptyRecord()
      records.set(name, record)
      return record
    }

    for (const line of input.split('\n')) {
      const [firstName, secondName, result] = line.split(';')
      const first = getRecord(firstName)
      const second = getRecord(secondName)

      if (result === 'draw') {
        first.drawn++
        second.drawn++
      } else if (result === 'win') {
        first.won++
        second.lost++
      } else if (result === 'loss') {
        first.lost++
        second.won++
      }

      first.played++
      second.played++
    }

    const rows = [...records.entries()]
      .sort(([firstName, first], [secondName, second]) => {
        const pointDifference =
          second.won * 3 +
          second.drawn -
          (first.won * 3 + first.drawn)
        return pointDifference || firstName.localeCompare(secondName)
      })
      .map(([name, record]) => formatRow(name, record))

    return [this.tableHeader, ...rows].join('\n')
  }
}
