'use client'

import { useState, useEffect } from 'react'
import {getRowCount} from './quote/action'

export function RowCounter(){
    const [count, setCount] = useState<number | null>(null)

    async function refreshCount() {
        const total = await getRowCount()
        setCount(total)
    }

    useEffect(() => {
        refreshCount()
    }, [])

    return (
        <span>{count === null ? 'Loading...' : count}</span>
    )
}