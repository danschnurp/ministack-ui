import { useQuery, useMutation } from '@tanstack/react-query'
import { listFunctions, invokeFunction, getFunctionLogs } from '../aws/lambda'

export const useLambdaFunctions = () =>
  useQuery({ queryKey: ['lambda-functions'], queryFn: listFunctions })

export const useLambdaInvocation = (functionName: string) =>
  useMutation({
    mutationFn: async () => invokeFunction(functionName),
    onSuccess: () => {
      // After invoking, you could fetch logs here
    },
  })

export const useLambdaLogs = (functionName: string) =>
  useQuery({ 
    queryKey: ['lambda-logs', functionName], 
    queryFn: () => getFunctionLogs(functionName), 
    enabled: !!functionName,
    refetchInterval: 2000,
  })
