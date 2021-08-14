# Version 1.0.2
# Types will be defined in CREEM Schema finally.
# Only for reference. Tabs stand for different type level.

	Any

		Bool
		String
		Number
		Array
		//Matrix
		Enum
		DateTime
		Struct
		Ref

		String
			StatusCode   -- StatusCode.csv
			QualifiedName
			LocalizedText
			Namespace
			UUID
			URI
			IPAddress
			MACAddress
			EMail

		Number
			Integer
				SByte
				Int16
				Int32
				Int64
			UInteger
				Byte
				UInt16, Word
				UInt32, DWord
				UInt64
			Double
			Float
			UNECE   -- UNECE.csv

		DateTime
			UtcTime

